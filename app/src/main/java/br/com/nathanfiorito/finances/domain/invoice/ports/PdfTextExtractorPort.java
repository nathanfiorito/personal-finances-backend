package br.com.nathanfiorito.finances.domain.invoice.ports;

public interface PdfTextExtractorPort {
    String extractText(byte[] pdfBytes);
}
