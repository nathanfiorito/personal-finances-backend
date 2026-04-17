package br.com.nathanfiorito.finances.infrastructure.invoice.adapter;

import br.com.nathanfiorito.finances.domain.invoice.exceptions.InvoiceImportException;
import br.com.nathanfiorito.finances.domain.invoice.ports.PdfTextExtractorPort;
import lombok.extern.slf4j.Slf4j;
import org.apache.pdfbox.Loader;
import org.apache.pdfbox.pdmodel.PDDocument;
import org.apache.pdfbox.text.PDFTextStripper;
import org.springframework.stereotype.Component;

import java.io.IOException;

@Slf4j
@Component
public class PdfBoxTextExtractorAdapter implements PdfTextExtractorPort {
    @Override
    public String extractText(byte[] pdfBytes) {
        try (PDDocument doc = Loader.loadPDF(pdfBytes)) {
            String text = new PDFTextStripper().getText(doc);
            log.debug("Extracted {} chars from PDF", text != null ? text.length() : 0);
            return text;
        } catch (IOException e) {
            throw new InvoiceImportException("Failed to extract PDF text: " + e.getMessage(), e);
        }
    }
}
