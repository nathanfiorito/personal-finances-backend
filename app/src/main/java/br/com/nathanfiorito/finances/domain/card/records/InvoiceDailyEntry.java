package br.com.nathanfiorito.finances.domain.card.records;

import java.math.BigDecimal;
import java.time.LocalDate;

public record InvoiceDailyEntry(
    LocalDate date,
    BigDecimal amount,
    BigDecimal accumulated
) {}
