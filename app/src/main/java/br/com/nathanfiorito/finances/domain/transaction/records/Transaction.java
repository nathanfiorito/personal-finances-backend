package br.com.nathanfiorito.finances.domain.transaction.records;

import br.com.nathanfiorito.finances.domain.transaction.enums.PaymentMethod;
import br.com.nathanfiorito.finances.domain.transaction.enums.TransactionType;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.UUID;

public record Transaction(
    UUID id,
    BigDecimal amount,
    LocalDate date,
    String establishment,
    String description,
    Integer categoryId,
    String category,
    String taxId,
    String entryType,
    TransactionType transactionType,
    PaymentMethod paymentMethod,
    Double confidence,
    LocalDateTime createdAt
) {}
