package br.com.nathanfiorito.finances.domain.card.records;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.List;

public record InvoiceTimeline(
    InvoicePeriodSummary current,
    InvoicePeriodSummary previous
) {
    public record InvoicePeriodSummary(
        LocalDate closingDate,
        LocalDate dueDate,
        BigDecimal total,
        List<InvoiceDailyEntry> daily
    ) {}
}
