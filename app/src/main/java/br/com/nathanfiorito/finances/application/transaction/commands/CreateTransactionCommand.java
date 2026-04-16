package br.com.nathanfiorito.finances.application.transaction.commands;

import br.com.nathanfiorito.finances.domain.transaction.enums.PaymentMethod;
import br.com.nathanfiorito.finances.domain.transaction.enums.TransactionType;

import java.math.BigDecimal;
import java.time.LocalDate;

public record CreateTransactionCommand(
    BigDecimal amount,
    LocalDate date,
    int categoryId,
    String entryType,
    TransactionType transactionType,
    PaymentMethod paymentMethod,
    String establishment,
    String description,
    String taxId,
    double confidence,
    Integer cardId
) {}
