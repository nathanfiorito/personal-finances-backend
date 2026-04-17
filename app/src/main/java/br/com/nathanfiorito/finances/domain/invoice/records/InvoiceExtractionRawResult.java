package br.com.nathanfiorito.finances.domain.invoice.records;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.List;

public record InvoiceExtractionRawResult(
    String cardLastFourDigits,
    List<Item> items
) {
    public record Item(
        LocalDate date,
        String establishment,
        String description,
        BigDecimal amount,
        Integer suggestedCategoryId,
        String suggestedCategoryName,
        String issuerHint,
        boolean isInternational,
        String originalCurrency,
        BigDecimal originalAmount,
        Double confidence
    ) {}
}
