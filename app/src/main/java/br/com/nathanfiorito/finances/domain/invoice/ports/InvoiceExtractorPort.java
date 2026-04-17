package br.com.nathanfiorito.finances.domain.invoice.ports;

import br.com.nathanfiorito.finances.domain.category.records.Category;
import br.com.nathanfiorito.finances.domain.invoice.records.InvoiceExtractionRawResult;

import java.util.List;

public interface InvoiceExtractorPort {
    InvoiceExtractionRawResult extract(String invoiceText, List<Category> activeCategories);
}
