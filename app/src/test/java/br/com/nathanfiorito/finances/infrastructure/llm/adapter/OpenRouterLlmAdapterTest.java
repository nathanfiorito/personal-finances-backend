package br.com.nathanfiorito.finances.infrastructure.llm.adapter;

import br.com.nathanfiorito.finances.domain.transaction.enums.PaymentMethod;
import br.com.nathanfiorito.finances.domain.transaction.enums.TransactionType;
import br.com.nathanfiorito.finances.domain.transaction.exceptions.LlmExtractionException;
import br.com.nathanfiorito.finances.domain.transaction.records.ExtractedTransaction;
import com.openai.models.chat.completions.StructuredChatCompletionCreateParams;
import io.opentelemetry.api.OpenTelemetry;
import io.opentelemetry.api.common.AttributeKey;
import io.opentelemetry.api.trace.StatusCode;
import io.opentelemetry.api.trace.Tracer;
import io.opentelemetry.sdk.testing.exporter.InMemorySpanExporter;
import io.opentelemetry.sdk.trace.SdkTracerProvider;
import io.opentelemetry.sdk.trace.data.SpanData;
import io.opentelemetry.sdk.trace.export.SimpleSpanProcessor;
import org.junit.jupiter.api.Test;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class OpenRouterLlmAdapterTest {

    // --- test helpers ---

    private static LlmExtractionResponse buildResponse(
            String amount, String date, String establishment,
            String description, String taxId,
            String transactionType, String paymentMethod, Double confidence) {
        LlmExtractionResponse r = new LlmExtractionResponse();
        r.amount = amount;
        r.date = date;
        r.establishment = establishment;
        r.description = description;
        r.taxId = taxId;
        r.transactionType = transactionType;
        r.paymentMethod = paymentMethod;
        r.confidence = confidence;
        return r;
    }

    /** Creates an adapter whose callLlm always returns the given LlmExtractionResponse. */
    private OpenRouterLlmAdapter adapterReturning(LlmExtractionResponse response) {
        return new OpenRouterLlmAdapter(null, OpenTelemetry.noop().getTracer("test")) {
            @Override
            @SuppressWarnings("unchecked")
            <T> LlmCallResult<T> callLlm(StructuredChatCompletionCreateParams<T> params) {
                return new LlmCallResult<>((T) response, 10L, 5L, "stop");
            }
        };
    }

    /** Creates an adapter whose callLlm always returns the given LlmDuplicateResponse. */
    private OpenRouterLlmAdapter adapterReturningDuplicate(boolean duplicate) {
        return new OpenRouterLlmAdapter(null, OpenTelemetry.noop().getTracer("test")) {
            @Override
            @SuppressWarnings("unchecked")
            <T> LlmCallResult<T> callLlm(StructuredChatCompletionCreateParams<T> params) {
                LlmDuplicateResponse r = new LlmDuplicateResponse();
                r.duplicate = duplicate;
                return new LlmCallResult<>((T) r, 10L, 5L, "stop");
            }
        };
    }

    // --- extractTransaction: text ---

    @Test
    void shouldExtractAllFieldsFromTextReceipt() {
        LlmExtractionResponse response = buildResponse(
            "50.00", "2026-01-15", "Supermercado Extra",
            "Compras da semana", "12.345.678/0001-99",
            "EXPENSE", "DEBIT", 0.95
        );
        OpenRouterLlmAdapter adapter = adapterReturning(response);

        ExtractedTransaction result = adapter.extractTransaction("receipt text content", "text");

        assertThat(result.amount()).isEqualByComparingTo(new BigDecimal("50.00"));
        assertThat(result.date()).isEqualTo(LocalDate.of(2026, 1, 15));
        assertThat(result.establishment()).isEqualTo("Supermercado Extra");
        assertThat(result.description()).isEqualTo("Compras da semana");
        assertThat(result.transactionType()).isEqualTo(TransactionType.EXPENSE);
        assertThat(result.paymentMethod()).isEqualTo(PaymentMethod.DEBIT);
        assertThat(result.confidence()).isEqualTo(0.95);
        assertThat(result.entryType()).isEqualTo("text");
    }

    @Test
    void shouldExtractTransactionFromPdf() {
        LlmExtractionResponse response = buildResponse(
            "120.50", "2026-02-10", "Posto Shell",
            null, null, "EXPENSE", "CREDIT", 0.88
        );
        OpenRouterLlmAdapter adapter = adapterReturning(response);

        ExtractedTransaction result = adapter.extractTransaction("extracted pdf content", "pdf");

        assertThat(result.amount()).isEqualByComparingTo(new BigDecimal("120.50"));
        assertThat(result.paymentMethod()).isEqualTo(PaymentMethod.CREDIT);
        assertThat(result.entryType()).isEqualTo("pdf");
        assertThat(result.description()).isNull();
    }

    @Test
    void shouldDefaultDateToTodayWhenResponseDateIsNull() {
        LlmExtractionResponse response = buildResponse(
            "30.00", null, "Padaria", null, null, "EXPENSE", null, 0.70
        );
        OpenRouterLlmAdapter adapter = adapterReturning(response);

        ExtractedTransaction result = adapter.extractTransaction("receipt text", "text");

        assertThat(result.date()).isEqualTo(LocalDate.now());
        assertThat(result.paymentMethod()).isNull();
    }

    @Test
    void shouldThrowIllegalArgumentExceptionForUnsupportedEntryType() {
        OpenRouterLlmAdapter adapter = adapterReturning(null);

        assertThatThrownBy(() -> adapter.extractTransaction("content", "manual"))
            .isInstanceOf(IllegalArgumentException.class)
            .hasMessageContaining("manual");
    }

    @Test
    void shouldThrowLlmExtractionExceptionWhenAmountIsUnparseable() {
        LlmExtractionResponse response = buildResponse(
            "not-a-number", "2026-01-01", "Store",
            null, null, "EXPENSE", null, 0.5
        );
        OpenRouterLlmAdapter adapter = adapterReturning(response);

        assertThatThrownBy(() -> adapter.extractTransaction("receipt", "text"))
            .isInstanceOf(LlmExtractionException.class);
    }

    // --- extractTransaction: image ---

    @Test
    void shouldExtractTransactionFromImage() {
        LlmExtractionResponse response = buildResponse(
            "89.90", "2026-03-20", "Restaurante Bom Sabor",
            "Almoço executivo", null, "EXPENSE", "CREDIT", 0.92
        );
        OpenRouterLlmAdapter adapter = adapterReturning(response);

        ExtractedTransaction result = adapter.extractTransaction(
            "base64EncodedImageData==", "image");

        assertThat(result.amount()).isEqualByComparingTo(new BigDecimal("89.90"));
        assertThat(result.establishment()).isEqualTo("Restaurante Bom Sabor");
        assertThat(result.entryType()).isEqualTo("image");
        assertThat(result.paymentMethod()).isEqualTo(PaymentMethod.CREDIT);
    }

    // --- isDuplicate ---

    private static ExtractedTransaction buildExtracted() {
        return new ExtractedTransaction(
            new BigDecimal("50.00"), LocalDate.of(2026, 1, 15),
            "Supermercado Extra", "Compras", null,
            "text", TransactionType.EXPENSE, PaymentMethod.DEBIT, 0.95
        );
    }

    @Test
    void isDuplicateShouldReturnTrueWhenLlmSaysDuplicate() {
        OpenRouterLlmAdapter adapter = adapterReturningDuplicate(true);

        boolean result = adapter.isDuplicate(buildExtracted(), List.of());

        assertThat(result).isTrue();
    }

    @Test
    void isDuplicateShouldReturnFalseWhenLlmSaysNotDuplicate() {
        OpenRouterLlmAdapter adapter = adapterReturningDuplicate(false);

        boolean result = adapter.isDuplicate(buildExtracted(), List.of());

        assertThat(result).isFalse();
    }

    @Test
    void isDuplicateShouldReturnFalseWhenLlmCallThrows() {
        OpenRouterLlmAdapter adapter = new OpenRouterLlmAdapter(null, OpenTelemetry.noop().getTracer("test")) {
            @Override
            <T> LlmCallResult<T> callLlm(StructuredChatCompletionCreateParams<T> params) {
                throw new RuntimeException("API unavailable");
            }
        };

        boolean result = adapter.isDuplicate(buildExtracted(), List.of());

        assertThat(result).isFalse();
    }

    // --- span tests ---

    private static Tracer tracerWithExporter(InMemorySpanExporter exporter) {
        SdkTracerProvider provider = SdkTracerProvider.builder()
            .addSpanProcessor(SimpleSpanProcessor.create(exporter))
            .build();
        return provider.get("test");
    }

    @Test
    void extractTransactionShouldCreateSpanWithLlmAttributes() {
        InMemorySpanExporter exporter = InMemorySpanExporter.create();
        Tracer tracer = tracerWithExporter(exporter);

        LlmExtractionResponse response = buildResponse(
            "50.00", "2026-01-15", "Store", null, null, "EXPENSE", null, 0.9
        );
        OpenRouterLlmAdapter adapter = new OpenRouterLlmAdapter(null, tracer) {
            @Override
            @SuppressWarnings("unchecked")
            <T> LlmCallResult<T> callLlm(StructuredChatCompletionCreateParams<T> params) {
                return new LlmCallResult<>((T) response, 100L, 50L, "stop");
            }
        };

        adapter.extractTransaction("some receipt text", "text");

        List<SpanData> spans = exporter.getFinishedSpanItems();
        assertThat(spans).hasSize(1);
        SpanData span = spans.get(0);
        assertThat(span.getName()).isEqualTo("llm.openrouter/extract");
        assertThat(span.getAttributes().get(AttributeKey.stringKey("llm.model")))
            .isEqualTo("anthropic/claude-haiku-4-5");
        assertThat(span.getAttributes().get(AttributeKey.stringKey("llm.operation")))
            .isEqualTo("extract");
        assertThat(span.getAttributes().get(AttributeKey.longKey("llm.input.tokens")))
            .isEqualTo(100L);
        assertThat(span.getAttributes().get(AttributeKey.longKey("llm.output.tokens")))
            .isEqualTo(50L);
        assertThat(span.getAttributes().get(AttributeKey.stringKey("llm.finish_reason")))
            .isEqualTo("stop");
        assertThat(span.getStatus().getStatusCode()).isEqualTo(StatusCode.UNSET);
    }

    @Test
    void extractTransactionShouldMarkSpanAsErrorWhenLlmThrows() {
        InMemorySpanExporter exporter = InMemorySpanExporter.create();
        Tracer tracer = tracerWithExporter(exporter);

        OpenRouterLlmAdapter adapter = new OpenRouterLlmAdapter(null, tracer) {
            @Override
            <T> LlmCallResult<T> callLlm(StructuredChatCompletionCreateParams<T> params) {
                throw new RuntimeException("LLM unavailable");
            }
        };

        assertThatThrownBy(() -> adapter.extractTransaction("text", "text"))
            .isInstanceOf(RuntimeException.class)
            .hasMessageContaining("LLM unavailable");

        SpanData span = exporter.getFinishedSpanItems().get(0);
        assertThat(span.getName()).isEqualTo("llm.openrouter/extract");
        assertThat(span.getStatus().getStatusCode()).isEqualTo(StatusCode.ERROR);
    }

    @Test
    void extractTransactionShouldUseVisionModelForImageEntryType() {
        InMemorySpanExporter exporter = InMemorySpanExporter.create();
        Tracer tracer = tracerWithExporter(exporter);

        LlmExtractionResponse response = buildResponse(
            "89.90", "2026-03-20", "Restaurante", null, null, "EXPENSE", "CREDIT", 0.92
        );
        OpenRouterLlmAdapter adapter = new OpenRouterLlmAdapter(null, tracer) {
            @Override
            @SuppressWarnings("unchecked")
            <T> LlmCallResult<T> callLlm(StructuredChatCompletionCreateParams<T> params) {
                return new LlmCallResult<>((T) response, 200L, 80L, "stop");
            }
        };

        adapter.extractTransaction("base64EncodedImage==", "image");

        SpanData span = exporter.getFinishedSpanItems().get(0);
        assertThat(span.getName()).isEqualTo("llm.openrouter/extract");
        assertThat(span.getAttributes().get(AttributeKey.stringKey("llm.model")))
            .isEqualTo("anthropic/claude-sonnet-4-6");
    }

    @Test
    void isDuplicateShouldMarkSpanAsErrorAndReturnFalseWhenLlmThrows() {
        InMemorySpanExporter exporter = InMemorySpanExporter.create();
        Tracer tracer = tracerWithExporter(exporter);

        OpenRouterLlmAdapter adapter = new OpenRouterLlmAdapter(null, tracer) {
            @Override
            <T> LlmCallResult<T> callLlm(StructuredChatCompletionCreateParams<T> params) {
                throw new RuntimeException("LLM unavailable");
            }
        };

        boolean result = adapter.isDuplicate(buildExtracted(), List.of());

        assertThat(result).isFalse();
        SpanData span = exporter.getFinishedSpanItems().get(0);
        assertThat(span.getName()).isEqualTo("llm.openrouter/isDuplicate");
        assertThat(span.getStatus().getStatusCode()).isEqualTo(StatusCode.ERROR);
    }
}
