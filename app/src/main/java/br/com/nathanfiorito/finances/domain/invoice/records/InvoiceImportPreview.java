package br.com.nathanfiorito.finances.domain.invoice.records;

import java.util.List;

public record InvoiceImportPreview(
    String sourceFileName,
    DetectedCard detectedCard,
    List<ExtractedInvoiceItem> items
) {}
