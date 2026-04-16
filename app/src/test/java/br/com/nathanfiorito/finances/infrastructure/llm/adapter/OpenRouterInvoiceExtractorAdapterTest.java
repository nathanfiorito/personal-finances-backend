package br.com.nathanfiorito.finances.infrastructure.llm.adapter;

import br.com.nathanfiorito.finances.domain.category.records.Category;
import br.com.nathanfiorito.finances.domain.invoice.exceptions.InvoiceImportException;
import br.com.nathanfiorito.finances.domain.invoice.records.InvoiceExtractionRawResult;
import com.openai.client.OpenAIClient;
import com.openai.models.chat.completions.StructuredChatCompletionCreateParams;
import io.opentelemetry.api.trace.Tracer;
import io.opentelemetry.api.trace.TracerProvider;
import org.junit.jupiter.api.Test;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.Mockito.mock;

class OpenRouterInvoiceExtractorAdapterTest {

    private final OpenAIClient client = mock(OpenAIClient.class);
    private final Tracer tracer = TracerProvider.noop().get("test");

    @Test
    void mapsHappyPath() {
        LlmInvoiceExtractionResponse payload = new LlmInvoiceExtractionResponse();
        payload.cardLastFourDigits = "7981";
        var item = new LlmInvoiceExtractionResponse.Item();
        item.date = "2025-12-28";
        item.establishment = "Google YouTube";
        item.amount = "1.99";
        item.isInternational = false;
        item.confidence = 0.9;
        item.suggestedCategoryId = 7;
        item.suggestedCategoryName = "Serviços";
        payload.items = List.of(item);

        OpenRouterInvoiceExtractorAdapter adapter = adapterReturning(payload);

        InvoiceExtractionRawResult result = adapter.extract("text", List.of(new Category(7, "Serviços", true)));

        assertThat(result.cardLastFourDigits()).isEqualTo("7981");
        assertThat(result.items()).hasSize(1);
        InvoiceExtractionRawResult.Item mapped = result.items().get(0);
        assertThat(mapped.date()).isEqualTo(LocalDate.parse("2025-12-28"));
        assertThat(mapped.establishment()).isEqualTo("Google YouTube");
        assertThat(mapped.amount()).isEqualByComparingTo(new BigDecimal("1.99"));
        assertThat(mapped.isInternational()).isFalse();
        assertThat(mapped.suggestedCategoryId()).isEqualTo(7);
    }

    @Test
    void throwsOnMalformedDate() {
        LlmInvoiceExtractionResponse payload = new LlmInvoiceExtractionResponse();
        payload.cardLastFourDigits = null;
        var item = new LlmInvoiceExtractionResponse.Item();
        item.date = "not-a-date";
        item.establishment = "X";
        item.amount = "1.00";
        payload.items = List.of(item);

        OpenRouterInvoiceExtractorAdapter adapter = adapterReturning(payload);

        assertThatThrownBy(() -> adapter.extract("text", List.of()))
            .isInstanceOf(InvoiceImportException.class)
            .hasMessageContaining("Failed to");
    }

    @Test
    void handlesNullItemsList() {
        LlmInvoiceExtractionResponse payload = new LlmInvoiceExtractionResponse();
        payload.cardLastFourDigits = "0000";
        payload.items = null;

        OpenRouterInvoiceExtractorAdapter adapter = adapterReturning(payload);

        InvoiceExtractionRawResult result = adapter.extract("text", List.of());
        assertThat(result.cardLastFourDigits()).isEqualTo("0000");
        assertThat(result.items()).isEmpty();
    }

    @Test
    void handlesEmptyItemsList() {
        LlmInvoiceExtractionResponse payload = new LlmInvoiceExtractionResponse();
        payload.cardLastFourDigits = "1234";
        payload.items = java.util.Collections.emptyList();

        OpenRouterInvoiceExtractorAdapter adapter = adapterReturning(payload);

        InvoiceExtractionRawResult result = adapter.extract("text", java.util.List.of());
        assertThat(result.cardLastFourDigits()).isEqualTo("1234");
        assertThat(result.items()).isEmpty();
    }

    @Test
    void throwsOnInvalidAmount() {
        LlmInvoiceExtractionResponse payload = new LlmInvoiceExtractionResponse();
        payload.cardLastFourDigits = null;
        var item = new LlmInvoiceExtractionResponse.Item();
        item.date = "2025-12-05";
        item.establishment = "X";
        item.amount = "not-a-number";
        payload.items = java.util.List.of(item);

        OpenRouterInvoiceExtractorAdapter adapter = adapterReturning(payload);

        assertThatThrownBy(() -> adapter.extract("text", java.util.List.of()))
            .isInstanceOf(InvoiceImportException.class)
            .hasMessageContaining("Failed to parse invoice line");
    }

    private OpenRouterInvoiceExtractorAdapter adapterReturning(LlmInvoiceExtractionResponse payload) {
        return new OpenRouterInvoiceExtractorAdapter(client, tracer) {
            @Override
            <T> LlmCallResult<T> callLlm(StructuredChatCompletionCreateParams<T> params) {
                @SuppressWarnings("unchecked")
                T typed = (T) payload;
                return new LlmCallResult<>(typed, 10, 20, "stop");
            }
        };
    }
}
