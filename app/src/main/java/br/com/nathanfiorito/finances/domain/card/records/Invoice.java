package br.com.nathanfiorito.finances.domain.card.records;

import br.com.nathanfiorito.finances.domain.transaction.records.Transaction;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.List;

public record Invoice(
    int cardId,
    LocalDate periodStart,
    LocalDate periodEnd,
    LocalDate closingDate,
    LocalDate dueDate,
    BigDecimal total,
    List<Transaction> transactions
) {}
