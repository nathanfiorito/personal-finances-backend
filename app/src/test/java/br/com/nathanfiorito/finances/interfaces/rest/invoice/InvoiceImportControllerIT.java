package br.com.nathanfiorito.finances.interfaces.rest.invoice;

import br.com.nathanfiorito.finances.application.invoice.usecases.ExtractInvoiceUseCase;
import br.com.nathanfiorito.finances.application.invoice.usecases.ImportInvoiceUseCase;
import br.com.nathanfiorito.finances.domain.invoice.exceptions.InvoiceImportException;
import br.com.nathanfiorito.finances.domain.invoice.records.DetectedCard;
import br.com.nathanfiorito.finances.domain.invoice.records.ExtractedInvoiceItem;
import br.com.nathanfiorito.finances.domain.invoice.records.InvoiceImportPreview;
import br.com.nathanfiorito.finances.interfaces.rest.BaseControllerIT;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.core.io.ClassPathResource;
import org.springframework.http.MediaType;
import org.springframework.mock.web.MockMultipartFile;
import org.springframework.test.context.bean.override.mockito.MockitoBean;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.multipart;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@WebMvcTest(InvoiceImportController.class)
class InvoiceImportControllerIT extends BaseControllerIT {

    @MockitoBean
    private ExtractInvoiceUseCase extractUseCase;

    @MockitoBean
    private ImportInvoiceUseCase importUseCase;

    @Autowired
    private ObjectMapper mapper;

    private InvoiceImportPreview samplePreview() {
        DetectedCard card = new DetectedCard("7981", 2, "Itaú Uniclass Black", "Itaú");
        ExtractedInvoiceItem item = new ExtractedInvoiceItem(
            "a1b2c3d4",
            LocalDate.of(2025, 12, 5),
            "TEST MERCHANT",
            null,
            new BigDecimal("10.00"),
            null,
            null,
            null,
            false,
            null,
            null,
            false,
            null,
            0.9
        );
        return new InvoiceImportPreview("fatura_sample.pdf", card, List.of(item));
    }

    @Test
    void previewReturnsExtractedItems() throws Exception {
        when(extractUseCase.execute(any(), any())).thenReturn(samplePreview());

        byte[] pdf = new ClassPathResource("fixtures/fatura_sample.pdf").getInputStream().readAllBytes();
        MockMultipartFile file = new MockMultipartFile(
            "file", "fatura_sample.pdf", MediaType.APPLICATION_PDF_VALUE, pdf);

        mockMvc.perform(multipart("/api/v1/invoices/import/preview")
                .file(file)
                .header("Authorization", validToken()))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.items[0].establishment").value("TEST MERCHANT"))
            .andExpect(jsonPath("$.items[0].temp_id").value("a1b2c3d4"))
            .andExpect(jsonPath("$.detected_card.last_four_digits").value("7981"));
    }

    @Test
    void previewRejectsNonPdf() throws Exception {
        MockMultipartFile file = new MockMultipartFile(
            "file", "x.txt", MediaType.TEXT_PLAIN_VALUE, "not a pdf".getBytes());

        mockMvc.perform(multipart("/api/v1/invoices/import/preview")
                .file(file)
                .header("Authorization", validToken()))
            .andExpect(status().isBadRequest());
    }

    @Test
    void previewReturnsUnauthorizedWhenTokenIsMissing() throws Exception {
        MockMultipartFile file = new MockMultipartFile(
            "file", "fatura_sample.pdf", MediaType.APPLICATION_PDF_VALUE, new byte[]{1, 2, 3});

        mockMvc.perform(multipart("/api/v1/invoices/import/preview")
                .file(file))
            .andExpect(status().isUnauthorized());
    }

    @Test
    void previewReturnsBadRequestWhenExtractorThrows() throws Exception {
        when(extractUseCase.execute(any(), any()))
            .thenThrow(new InvoiceImportException("PDF has no extractable text"));

        byte[] pdf = new ClassPathResource("fixtures/fatura_sample.pdf").getInputStream().readAllBytes();
        MockMultipartFile file = new MockMultipartFile(
            "file", "fatura_sample.pdf", MediaType.APPLICATION_PDF_VALUE, pdf);

        mockMvc.perform(multipart("/api/v1/invoices/import/preview")
                .file(file)
                .header("Authorization", validToken()))
            .andExpect(status().isBadRequest());
    }

    @Test
    void importPersistsAllRowsAndReturnsIds() throws Exception {
        UUID id1 = UUID.fromString("00000000-0000-0000-0000-000000000001");
        when(importUseCase.execute(any())).thenReturn(List.of(id1));

        var body = Map.of(
            "card_id", 2,
            "items", List.of(Map.of(
                "date", "2025-12-05",
                "establishment", "TEST",
                "amount", "10.00",
                "category_id", 7)));

        mockMvc.perform(post("/api/v1/invoices/import")
                .header("Authorization", validToken())
                .contentType(MediaType.APPLICATION_JSON)
                .content(mapper.writeValueAsString(body)))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.imported_count").value(1))
            .andExpect(jsonPath("$.card_id").value(2))
            .andExpect(jsonPath("$.transaction_ids[0]").value(id1.toString()));
    }

    @Test
    void importReturnsBadRequestWhenCardIdIsMissing() throws Exception {
        var body = Map.of(
            "items", List.of(Map.of(
                "date", "2025-12-05",
                "establishment", "TEST",
                "amount", "10.00",
                "category_id", 7)));

        mockMvc.perform(post("/api/v1/invoices/import")
                .header("Authorization", validToken())
                .contentType(MediaType.APPLICATION_JSON)
                .content(mapper.writeValueAsString(body)))
            .andExpect(status().isBadRequest());
    }

    @Test
    void importReturnsBadRequestWhenImportUseCaseThrows() throws Exception {
        when(importUseCase.execute(any()))
            .thenThrow(new InvoiceImportException("Card not found: 999"));

        var body = Map.of(
            "card_id", 999,
            "items", List.of(Map.of(
                "date", "2025-12-05",
                "establishment", "TEST",
                "amount", "10.00",
                "category_id", 7)));

        mockMvc.perform(post("/api/v1/invoices/import")
                .header("Authorization", validToken())
                .contentType(MediaType.APPLICATION_JSON)
                .content(mapper.writeValueAsString(body)))
            .andExpect(status().isBadRequest());
    }

    @Test
    void importReturnsUnauthorizedWhenTokenIsMissing() throws Exception {
        mockMvc.perform(post("/api/v1/invoices/import")
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"card_id\":1,\"items\":[]}"))
            .andExpect(status().isUnauthorized());
    }

    @Test
    void previewReturnsBadRequestWhenFileIsEmpty() throws Exception {
        MockMultipartFile file = new MockMultipartFile(
            "file", "empty.pdf", MediaType.APPLICATION_PDF_VALUE, new byte[0]);

        mockMvc.perform(multipart("/api/v1/invoices/import/preview")
                .file(file)
                .header("Authorization", validToken()))
            .andExpect(status().isBadRequest());
    }

    @Test
    void importReturnsBadRequestWhenItemsListIsEmpty() throws Exception {
        var body = Map.of(
            "card_id", 2,
            "items", List.of());

        mockMvc.perform(post("/api/v1/invoices/import")
                .header("Authorization", validToken())
                .contentType(MediaType.APPLICATION_JSON)
                .content(mapper.writeValueAsString(body)))
            .andExpect(status().isBadRequest());
    }
}
