package br.com.nathanfiorito.finances.infrastructure.llm.adapter;

import br.com.nathanfiorito.finances.domain.card.records.InvoicePrediction;
import br.com.nathanfiorito.finances.domain.transaction.enums.PaymentMethod;
import br.com.nathanfiorito.finances.domain.transaction.enums.TransactionType;
import br.com.nathanfiorito.finances.domain.transaction.exceptions.LlmExtractionException;
import br.com.nathanfiorito.finances.domain.transaction.ports.LlmPort;
import br.com.nathanfiorito.finances.domain.transaction.records.ExtractedTransaction;
import br.com.nathanfiorito.finances.domain.transaction.records.Transaction;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;
import com.openai.client.OpenAIClient;
import com.openai.core.JsonSchemaLocalValidation;
import com.openai.models.chat.completions.ChatCompletionContentPart;
import com.openai.models.chat.completions.ChatCompletionContentPartImage;
import com.openai.models.chat.completions.ChatCompletionContentPartText;
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
import java.util.List;

@Component
@RequiredArgsConstructor
public class OpenRouterLlmAdapter implements LlmPort {

    private static final String HAIKU  = "anthropic/claude-haiku-4-5";
    private static final String SONNET = "anthropic/claude-sonnet-4-6";

    private static final ObjectMapper MAPPER = new ObjectMapper()
        .registerModule(new JavaTimeModule());

    private final OpenAIClient client;
    private final Tracer tracer;

    // -------------------------------------------------------------------------
    // LlmPort
    // -------------------------------------------------------------------------

    @Override
    public ExtractedTransaction extractTransaction(String content, String entryType) {
        String model = "image".equals(entryType) ? SONNET : HAIKU;
        Span span = tracer.spanBuilder("llm.openrouter/extract")
            .setAttribute("llm.model", model)
            .setAttribute("llm.operation", "extract")
            .startSpan();
        try (Scope scope = span.makeCurrent()) {
            LlmCallResult<LlmExtractionResponse> result = switch (entryType) {
                case "text", "pdf" -> callLlm(
                    ChatCompletionCreateParams.builder()
                        .model(HAIKU)
                        .addUserMessage(buildTextPrompt(content))
                        .responseFormat(LlmExtractionResponse.class, JsonSchemaLocalValidation.NO)
                        .build());
                case "image" -> callLlm(buildImageParams(content));
                default -> throw new IllegalArgumentException(
                    "Unsupported entry type: " + entryType);
            };
            span.setAttribute("llm.input.tokens", result.inputTokens());
            span.setAttribute("llm.output.tokens", result.outputTokens());
            span.setAttribute("llm.finish_reason", result.finishReason());
            return mapToExtracted(result.content(), entryType);
        } catch (Exception e) {
            span.setStatus(StatusCode.ERROR, e.getMessage());
            span.recordException(e);
            throw e;
        } finally {
            span.end();
        }
    }

    @Override
    public String categorize(ExtractedTransaction extracted, List<String> categoryNames) {
        if (categoryNames.isEmpty()) return "Outros";
        Span span = tracer.spanBuilder("llm.openrouter/categorize")
            .setAttribute("llm.model", HAIKU)
            .setAttribute("llm.operation", "categorize")
            .startSpan();
        try (Scope scope = span.makeCurrent()) {
            StructuredChatCompletionCreateParams<LlmCategorizeResponse> params =
                ChatCompletionCreateParams.builder()
                    .model(HAIKU)
                    .addUserMessage(buildCategorizePrompt(extracted, categoryNames))
                    .responseFormat(LlmCategorizeResponse.class, JsonSchemaLocalValidation.NO)
                    .build();
            LlmCallResult<LlmCategorizeResponse> result = callLlm(params);
            span.setAttribute("llm.input.tokens", result.inputTokens());
            span.setAttribute("llm.output.tokens", result.outputTokens());
            span.setAttribute("llm.finish_reason", result.finishReason());
            if (result.content() != null && result.content().category != null
                    && categoryNames.contains(result.content().category)) {
                return result.content().category;
            }
        } catch (Exception e) {
            span.setStatus(StatusCode.ERROR, e.getMessage());
            span.recordException(e);
        } finally {
            span.end();
        }
        return categoryNames.get(0);
    }

    @Override
    public boolean isDuplicate(ExtractedTransaction extracted, List<Transaction> recentTransactions) {
        Span span = tracer.spanBuilder("llm.openrouter/isDuplicate")
            .setAttribute("llm.model", HAIKU)
            .setAttribute("llm.operation", "isDuplicate")
            .startSpan();
        try (Scope scope = span.makeCurrent()) {
            StructuredChatCompletionCreateParams<LlmDuplicateResponse> params =
                ChatCompletionCreateParams.builder()
                    .model(HAIKU)
                    .addUserMessage(buildDuplicatePrompt(extracted, recentTransactions))
                    .responseFormat(LlmDuplicateResponse.class, JsonSchemaLocalValidation.NO)
                    .build();
            LlmCallResult<LlmDuplicateResponse> result = callLlm(params);
            span.setAttribute("llm.input.tokens", result.inputTokens());
            span.setAttribute("llm.output.tokens", result.outputTokens());
            span.setAttribute("llm.finish_reason", result.finishReason());
            return result.content() != null && result.content().duplicate;
        } catch (Exception e) {
            span.setStatus(StatusCode.ERROR, e.getMessage());
            span.recordException(e);
            return false;
        } finally {
            span.end();
        }
    }

    @Override
    public InvoicePrediction generateInvoicePrediction(int cardId, BigDecimal currentTotal,
            int transactionCount, int daysElapsed, int daysRemaining,
            List<BigDecimal> historicalTotals) {
        Span span = tracer.spanBuilder("llm.openrouter/predict")
            .setAttribute("llm.model", HAIKU)
            .setAttribute("llm.operation", "predict")
            .startSpan();
        try (Scope scope = span.makeCurrent()) {
            StructuredChatCompletionCreateParams<LlmPredictionResponse> params =
                ChatCompletionCreateParams.builder()
                    .model(HAIKU)
                    .addUserMessage(buildPredictionPrompt(currentTotal, transactionCount,
                        daysElapsed, daysRemaining, historicalTotals))
                    .responseFormat(LlmPredictionResponse.class, JsonSchemaLocalValidation.NO)
                    .build();
            LlmCallResult<LlmPredictionResponse> result = callLlm(params);
            span.setAttribute("llm.input.tokens", result.inputTokens());
            span.setAttribute("llm.output.tokens", result.outputTokens());
            span.setAttribute("llm.finish_reason", result.finishReason());
            return mapToPrediction(cardId, currentTotal, daysRemaining, historicalTotals, result.content());
        } catch (Exception e) {
            span.setStatus(StatusCode.ERROR, e.getMessage());
            span.recordException(e);
            throw new LlmExtractionException("Failed to generate invoice prediction: " + e.getMessage(), e);
        } finally {
            span.end();
        }
    }

    // -------------------------------------------------------------------------
    // Package-private — overridden by anonymous subclasses in tests
    // -------------------------------------------------------------------------

    <T> LlmCallResult<T> callLlm(StructuredChatCompletionCreateParams<T> params) {
        var completion = client.chat().completions().create(params);
        T content = completion.choices().stream()
            .flatMap(choice -> choice.message().content().stream())
            .findFirst()
            .orElseThrow(() -> new LlmExtractionException("Empty response from LLM"));
        long inputTokens = completion.usage()
            .map(u -> u.promptTokens())
            .orElse(0L);
        long outputTokens = completion.usage()
            .map(u -> u.completionTokens())
            .orElse(0L);
        String finishReason = completion.choices().stream()
            .findFirst()
            .map(c -> c.finishReason().toString())
            .orElse("unknown");
        return new LlmCallResult<>(content, inputTokens, outputTokens, finishReason);
    }

    // -------------------------------------------------------------------------
    // Private: image params builder
    // -------------------------------------------------------------------------

    /** Builds the multimodal params for image extraction. */
    private StructuredChatCompletionCreateParams<LlmExtractionResponse> buildImageParams(String base64Content) {
        ChatCompletionContentPartText textPart = ChatCompletionContentPartText.builder()
            .text(buildImagePrompt())
            .build();
        // Telegram photo messages are always delivered as JPEG.
        ChatCompletionContentPartImage imagePart = ChatCompletionContentPartImage.builder()
            .imageUrl(ChatCompletionContentPartImage.ImageUrl.builder()
                .url("data:image/jpeg;base64," + base64Content)
                .build())
            .build();
        return ChatCompletionCreateParams.builder()
            .model(SONNET)
            .addUserMessageOfArrayOfContentParts(List.of(
                ChatCompletionContentPart.ofText(textPart),
                ChatCompletionContentPart.ofImageUrl(imagePart)
            ))
            .responseFormat(LlmExtractionResponse.class, JsonSchemaLocalValidation.NO)
            .build();
    }

    // -------------------------------------------------------------------------
    // Private: mapping
    // -------------------------------------------------------------------------

    private ExtractedTransaction mapToExtracted(LlmExtractionResponse r, String entryType) {
        try {
            BigDecimal amount = new BigDecimal(r.amount);
            LocalDate date = (r.date != null) ? LocalDate.parse(r.date) : LocalDate.now();
            TransactionType transactionType = TransactionType.valueOf(r.transactionType);
            PaymentMethod paymentMethod = (r.paymentMethod != null)
                ? PaymentMethod.valueOf(r.paymentMethod) : null;
            double confidence = (r.confidence != null) ? r.confidence : 0.0;
            return new ExtractedTransaction(
                amount, date, r.establishment, r.description,
                r.taxId, entryType, transactionType, paymentMethod, confidence
            );
        } catch (Exception e) {
            throw new LlmExtractionException("Failed to map LLM response: " + e.getMessage(), e);
        }
    }

    // -------------------------------------------------------------------------
    // Private: prompt builders
    // -------------------------------------------------------------------------

    private String buildTextPrompt(String content) {
        return """
            You are a financial assistant. Extract expense details from the following receipt.

            Receipt:
            %s

            Return a JSON object with these exact fields:
            - amount: transaction amount as a decimal string (e.g. "50.00"), required
            - date: date in YYYY-MM-DD format, or null if not found
            - establishment: merchant or business name, or null
            - description: brief purchase description, or null
            - tax_id: merchant CNPJ (digits only or formatted), or null
            - transaction_type: "EXPENSE" or "INCOME"
            - payment_method: "CREDIT" or "DEBIT", or null if not determinable
            - confidence: your extraction confidence from 0.0 to 1.0
            """.formatted(content);
    }

    private String buildImagePrompt() {
        return """
            You are a financial assistant. Extract expense details from the receipt image.

            Return a JSON object with these exact fields:
            - amount: transaction amount as a decimal string (e.g. "50.00"), required
            - date: date in YYYY-MM-DD format, or null if not found
            - establishment: merchant or business name, or null
            - description: brief purchase description, or null
            - tax_id: merchant CNPJ (digits only or formatted), or null
            - transaction_type: "EXPENSE" or "INCOME"
            - payment_method: "CREDIT" or "DEBIT", or null if not determinable
            - confidence: your extraction confidence from 0.0 to 1.0
            """;
    }

    private String buildCategorizePrompt(ExtractedTransaction extracted, List<String> categoryNames) {
        try {
            String extractedJson = MAPPER.writeValueAsString(extracted);
            return """
                You are a financial assistant. Categorize the following transaction.

                Transaction:
                %s

                Available categories: %s

                Choose the single category that best matches this transaction.
                Return exactly: {"category": "<chosen category name>"}
                You must choose from the available categories list.
                """.formatted(extractedJson, String.join(", ", categoryNames));
        } catch (JsonProcessingException e) {
            throw new LlmExtractionException("Failed to serialize transaction for categorization", e);
        }
    }

    private String buildDuplicatePrompt(ExtractedTransaction extracted,
                                        List<Transaction> recentTransactions) {
        try {
            String extractedJson = MAPPER.writeValueAsString(extracted);
            String recentJson    = MAPPER.writeValueAsString(recentTransactions);
            return """
                You are a financial assistant. Check if the new transaction is a duplicate.

                New transaction:
                %s

                Recent transactions:
                %s

                A duplicate has the same amount, date, and merchant as an existing entry.
                Return exactly: {"duplicate": true} or {"duplicate": false}
                """.formatted(extractedJson, recentJson);
        } catch (JsonProcessingException e) {
            throw new LlmExtractionException(
                "Failed to serialize transactions for duplicate check", e);
        }
    }

    private String buildPredictionPrompt(BigDecimal currentTotal, int transactionCount,
                                         int daysElapsed, int daysRemaining,
                                         List<BigDecimal> historicalTotals) {
        String historicalStr = historicalTotals.stream()
            .map(BigDecimal::toPlainString)
            .reduce((a, b) -> a + ", " + b)
            .orElse("none");
        return """
            You are a financial assistant. Predict the final invoice total for a credit card.

            Current invoice status:
            - Current total: R$ %s
            - Transactions so far: %d
            - Days elapsed in period: %d
            - Days remaining in period: %d

            Historical invoice totals (most recent first): [%s]

            Based on spending patterns and historical data, predict:
            1. The final total when the invoice closes
            2. Your confidence level (low, medium, high)
            3. The projected remaining spend

            Return a JSON object with these exact fields:
            - predicted_total: predicted final total as a decimal string (e.g. "1500.00")
            - confidence: "low", "medium", or "high"
            - projected_remaining: predicted remaining spend as a decimal string
            - based_on_invoices: number of historical invoices used for prediction
            """.formatted(currentTotal.toPlainString(), transactionCount,
                daysElapsed, daysRemaining, historicalStr);
    }

    private InvoicePrediction mapToPrediction(int cardId, BigDecimal currentTotal,
                                              int daysRemaining, List<BigDecimal> historicalTotals,
                                              LlmPredictionResponse response) {
        BigDecimal predictedTotal = new BigDecimal(response.predictedTotal);
        BigDecimal projectedRemaining = new BigDecimal(response.projectedRemaining);
        String confidence = response.confidence != null ? response.confidence : "low";
        int basedOnInvoices = response.basedOnInvoices;

        BigDecimal dailyAverage = BigDecimal.ZERO;
        if (!historicalTotals.isEmpty()) {
            BigDecimal sum = historicalTotals.stream().reduce(BigDecimal.ZERO, BigDecimal::add);
            dailyAverage = sum.divide(BigDecimal.valueOf(historicalTotals.size() * 30L), 2,
                java.math.RoundingMode.HALF_UP);
        }

        return new InvoicePrediction(
            cardId, predictedTotal, currentTotal, daysRemaining,
            dailyAverage, java.time.LocalDateTime.now(), confidence,
            projectedRemaining, basedOnInvoices
        );
    }
}
