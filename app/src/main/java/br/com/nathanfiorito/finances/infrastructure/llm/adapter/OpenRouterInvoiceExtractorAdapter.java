package br.com.nathanfiorito.finances.infrastructure.llm.adapter;

import br.com.nathanfiorito.finances.domain.category.records.Category;
import br.com.nathanfiorito.finances.domain.invoice.exceptions.InvoiceImportException;
import br.com.nathanfiorito.finances.domain.invoice.ports.InvoiceExtractorPort;
import br.com.nathanfiorito.finances.domain.invoice.records.InvoiceExtractionRawResult;
import com.openai.client.OpenAIClient;
import com.openai.core.JsonSchemaLocalValidation;
import com.openai.models.chat.completions.ChatCompletionCreateParams;
import com.openai.models.chat.completions.StructuredChatCompletionCreateParams;
import io.opentelemetry.api.trace.Span;
import io.opentelemetry.api.trace.StatusCode;
import io.opentelemetry.api.trace.Tracer;
import io.opentelemetry.context.Scope;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Component;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;

@Component
@RequiredArgsConstructor
public class OpenRouterInvoiceExtractorAdapter implements InvoiceExtractorPort {

    private static final String HAIKU = "anthropic/claude-haiku-4-5";

    private final OpenAIClient client;
    private final Tracer tracer;

    @Override
    public InvoiceExtractionRawResult extract(String invoiceText, List<Category> activeCategories) {
        Span span = tracer.spanBuilder("llm.openrouter/invoice.extract")
            .setAttribute("llm.model", HAIKU)
            .setAttribute("llm.operation", "invoice.extract")
            .setAttribute("invoice.input_chars", invoiceText.length())
            .startSpan();
        try (Scope scope = span.makeCurrent()) {
            StructuredChatCompletionCreateParams<LlmInvoiceExtractionResponse> params =
                ChatCompletionCreateParams.builder()
                    .model(HAIKU)
                    .addUserMessage(buildPrompt(invoiceText, activeCategories))
                    .responseFormat(LlmInvoiceExtractionResponse.class, JsonSchemaLocalValidation.NO)
                    .build();
            LlmCallResult<LlmInvoiceExtractionResponse> result = callLlm(params);
            span.setAttribute("llm.input.tokens", result.inputTokens());
            span.setAttribute("llm.output.tokens", result.outputTokens());
            span.setAttribute("llm.finish_reason", result.finishReason());
            InvoiceExtractionRawResult mapped = map(result.content());
            span.setAttribute("invoice.items_count", mapped.items().size());
            return mapped;
        } catch (Exception e) {
            span.setStatus(StatusCode.ERROR, e.getMessage());
            span.recordException(e);
            if (e instanceof InvoiceImportException) {
                throw (InvoiceImportException) e;
            }
            throw new InvoiceImportException("Failed to extract invoice via LLM: " + e.getMessage(), e);
        } finally {
            span.end();
        }
    }

    /** Package-private — overridden in unit tests. */
    <T> LlmCallResult<T> callLlm(StructuredChatCompletionCreateParams<T> params) {
        var completion = client.chat().completions().create(params);
        T content = completion.choices().stream()
            .flatMap(choice -> choice.message().content().stream())
            .findFirst()
            .orElseThrow(() -> new InvoiceImportException("Empty response from LLM"));
        long inputTokens  = completion.usage().map(u -> u.promptTokens()).orElse(0L);
        long outputTokens = completion.usage().map(u -> u.completionTokens()).orElse(0L);
        String finishReason = completion.choices().stream()
            .findFirst().map(c -> c.finishReason().toString()).orElse("unknown");
        return new LlmCallResult<>(content, inputTokens, outputTokens, finishReason);
    }

    private String buildPrompt(String invoiceText, List<Category> categories) {
        StringBuilder categoryList = new StringBuilder();
        for (Category c : categories) {
            categoryList.append("- id=").append(c.id()).append(" name=\"").append(c.name()).append("\"\n");
        }
        return """
            You are a financial assistant. Extract line items from a Brazilian credit-card invoice (fatura) PDF text.

            Categories available (use only these IDs):
            %s

            Rules:
            - Extract the card's last 4 digits from the header if present (look for "Cartão NNNN.XXXX.XXXX.NNNN" or similar). Return in `card_last_four_digits`. `null` if not found.
            - Extract ONLY line items that represent the cardholder's spending in the period: domestic purchases, international purchases (in BRL after conversion), and card products/services (e.g. SEG CARTAO PROTEGIDO).
            - IGNORE: payment of previous invoice (lines starting with "PAGAMENTO" with negative value), installments for future invoices ("Compras parceladas - próximas faturas"), totals, subtotals, and charges that are zero.
            - Dates must be ISO-8601 (YYYY-MM-DD). Infer the year from the invoice header ("Emissão" / "Vencimento"), NOT from today.
            - Amounts are always positive BRL decimals as strings (e.g. "112.20"). Use a dot as decimal separator.
            - For international rows: `is_international=true`, and fill `original_currency` and `original_amount` if readable; otherwise null. The `amount` is the BRL value (converted).
            - Map the issuer hint (e.g. "saúde", "restaurante") to one of the provided category IDs. If none fits confidently, return `suggested_category_id=null`.
            - `confidence`: 0.0-1.0 per row.

            Return a JSON object with exactly these fields:
            {
              "card_last_four_digits": "NNNN" | null,
              "items": [
                {
                  "date": "YYYY-MM-DD",
                  "establishment": "string",
                  "description": "string" | null,
                  "amount": "decimal string",
                  "suggested_category_id": integer | null,
                  "suggested_category_name": "string" | null,
                  "issuer_hint": "string" | null,
                  "is_international": boolean,
                  "original_currency": "USD" | null,
                  "original_amount": "decimal string" | null,
                  "confidence": 0.95
                }
              ]
            }

            Invoice text:
            %s
            """.formatted(categoryList.toString(), invoiceText);
    }

    private InvoiceExtractionRawResult map(LlmInvoiceExtractionResponse response) {
        List<InvoiceExtractionRawResult.Item> items = new ArrayList<>();
        if (response.items != null) {
            for (LlmInvoiceExtractionResponse.Item raw : response.items) {
                try {
                    items.add(new InvoiceExtractionRawResult.Item(
                        LocalDate.parse(raw.date),
                        raw.establishment,
                        raw.description,
                        new BigDecimal(raw.amount),
                        raw.suggestedCategoryId,
                        raw.suggestedCategoryName,
                        raw.issuerHint,
                        raw.isInternational != null && raw.isInternational,
                        raw.originalCurrency,
                        raw.originalAmount != null ? new BigDecimal(raw.originalAmount) : null,
                        raw.confidence != null ? raw.confidence : 0.0
                    ));
                } catch (Exception e) {
                    throw new InvoiceImportException(
                        "Failed to parse invoice line (establishment=" + raw.establishment + "): " + e.getMessage(), e);
                }
            }
        }
        return new InvoiceExtractionRawResult(response.cardLastFourDigits, items);
    }
}
