package br.com.nathanfiorito.finances.infrastructure.llm.adapter;

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

    // -------------------------------------------------------------------------
    // LlmPort
    // -------------------------------------------------------------------------

    @Override
    public ExtractedTransaction extractTransaction(String content, String entryType) {
        return switch (entryType) {
            case "text", "pdf" -> extractFromText(content, entryType);
            case "image"       -> extractFromImage(content);
            default            -> throw new IllegalArgumentException(
                "Unsupported entry type: " + entryType);
        };
    }

    @Override
    public boolean isDuplicate(ExtractedTransaction extracted, List<Transaction> recentTransactions) {
        String prompt = buildDuplicatePrompt(extracted, recentTransactions);
        StructuredChatCompletionCreateParams<LlmDuplicateResponse> params =
            ChatCompletionCreateParams.builder()
                .model(HAIKU)
                .addUserMessage(prompt)
                .responseFormat(LlmDuplicateResponse.class, JsonSchemaLocalValidation.NO)
                .build();
        try {
            LlmDuplicateResponse response = callLlm(params);
            return response != null && response.duplicate;
        } catch (Exception e) {
            return false; // safe default — prefer saving over silently dropping
        }
    }

    // -------------------------------------------------------------------------
    // Package-private — overridden by anonymous subclasses in tests
    // -------------------------------------------------------------------------

    <T> T callLlm(StructuredChatCompletionCreateParams<T> params) {
        return client.chat().completions().create(params)
            .choices().stream()
            .flatMap(choice -> choice.message().content().stream())
            .findFirst()
            .orElseThrow(() -> new LlmExtractionException("Empty response from LLM"));
    }

    // -------------------------------------------------------------------------
    // Private: extraction helpers
    // -------------------------------------------------------------------------

    private ExtractedTransaction extractFromText(String content, String entryType) {
        StructuredChatCompletionCreateParams<LlmExtractionResponse> params =
            ChatCompletionCreateParams.builder()
                .model(HAIKU)
                .addUserMessage(buildTextPrompt(content))
                .responseFormat(LlmExtractionResponse.class, JsonSchemaLocalValidation.NO)
                .build();
        return mapToExtracted(callLlm(params), entryType);
    }

    private ExtractedTransaction extractFromImage(String base64Content) {
        StructuredChatCompletionCreateParams<LlmExtractionResponse> params =
            buildImageParams(base64Content);
        return mapToExtracted(callLlm(params), "image");
    }

    /** Builds the multimodal params for image extraction. */
    StructuredChatCompletionCreateParams<LlmExtractionResponse> buildImageParams(String base64Content) {
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
}
