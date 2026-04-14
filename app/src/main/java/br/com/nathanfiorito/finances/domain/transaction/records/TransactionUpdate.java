package br.com.nathanfiorito.finances.domain.transaction.records;

import br.com.nathanfiorito.finances.domain.transaction.enums.PaymentMethod;
import br.com.nathanfiorito.finances.domain.transaction.enums.TransactionType;

import java.math.BigDecimal;
import java.time.LocalDate;

public record TransactionUpdate(
    BigDecimal amount,
    LocalDate date,
    String establishment,
    String description,
    Integer categoryId,
    PaymentMethod paymentMethod,
    TransactionType transactionType
) {}
