package br.com.nathanfiorito.finances.infrastructure.invoice.adapter;

import br.com.nathanfiorito.finances.domain.invoice.exceptions.InvoiceImportException;
import org.apache.pdfbox.pdmodel.PDDocument;
import org.apache.pdfbox.pdmodel.PDPage;
import org.apache.pdfbox.pdmodel.PDPageContentStream;
import org.apache.pdfbox.pdmodel.font.PDType1Font;
import org.apache.pdfbox.pdmodel.font.Standard14Fonts;
import org.junit.jupiter.api.Test;

import java.io.ByteArrayOutputStream;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class PdfBoxTextExtractorAdapterTest {

    private final PdfBoxTextExtractorAdapter adapter = new PdfBoxTextExtractorAdapter();

    @Test
    void extractsTextFromSimplePdf() throws Exception {
        byte[] pdfBytes = buildPdfWithText("Hello PDFBox");

        String text = adapter.extractText(pdfBytes);

        assertThat(text).contains("Hello PDFBox");
    }

    @Test
    void throwsInvoiceImportExceptionOnInvalidBytes() {
        byte[] notAPdf = "not a pdf at all".getBytes();

        assertThatThrownBy(() -> adapter.extractText(notAPdf))
            .isInstanceOf(InvoiceImportException.class)
            .hasMessageContaining("Failed to extract PDF text");
    }

    private byte[] buildPdfWithText(String text) throws Exception {
        try (PDDocument doc = new PDDocument(); ByteArrayOutputStream out = new ByteArrayOutputStream()) {
            PDPage page = new PDPage();
            doc.addPage(page);
            try (PDPageContentStream cs = new PDPageContentStream(doc, page)) {
                cs.setFont(new PDType1Font(Standard14Fonts.FontName.HELVETICA), 12);
                cs.beginText();
                cs.newLineAtOffset(50, 700);
                cs.showText(text);
                cs.endText();
            }
            doc.save(out);
            return out.toByteArray();
        }
    }
}
