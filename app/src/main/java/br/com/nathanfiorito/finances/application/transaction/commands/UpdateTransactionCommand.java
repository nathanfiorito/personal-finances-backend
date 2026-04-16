package br.com.nathanfiorito.finances.application.transaction.commands;

import br.com.nathanfiorito.finances.domain.transaction.enums.PaymentMethod;
import br.com.nathanfiorito.finances.domain.transaction.enums.TransactionType;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.UUID;

public record UpdateTransactionCommand(
    UUID id,
    BigDecimal amount,
    LocalDate date,
    String establishment,
    String description,
    Integer categoryId,
    PaymentMethod paymentMethod,
    TransactionType transactionType,
    Integer cardId
) {}
