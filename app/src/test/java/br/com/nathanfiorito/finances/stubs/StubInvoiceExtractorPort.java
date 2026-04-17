package br.com.nathanfiorito.finances.stubs;

import br.com.nathanfiorito.finances.domain.category.records.Category;
import br.com.nathanfiorito.finances.domain.invoice.ports.InvoiceExtractorPort;
import br.com.nathanfiorito.finances.domain.invoice.records.InvoiceExtractionRawResult;

import java.util.List;

public class StubInvoiceExtractorPort implements InvoiceExtractorPort {

    private InvoiceExtractionRawResult nextResult;
    private RuntimeException nextFailure;

    public void willReturn(InvoiceExtractionRawResult result) {
        this.nextResult = result;
        this.nextFailure = null;
    }

    public void willFailWith(RuntimeException e) {
        this.nextFailure = e;
        this.nextResult = null;
    }

    @Override
    public InvoiceExtractionRawResult extract(String invoiceText, List<Category> activeCategories) {
        if (nextFailure != null) throw nextFailure;
        if (nextResult == null) {
            throw new IllegalStateException("StubInvoiceExtractorPort was called but no result was configured");
        }
        return nextResult;
    }
}
