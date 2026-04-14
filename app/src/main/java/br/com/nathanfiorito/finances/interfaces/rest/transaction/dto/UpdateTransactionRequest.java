package br.com.nathanfiorito.finances.interfaces.rest.transaction.dto;

import br.com.nathanfiorito.finances.application.transaction.commands.UpdateTransactionCommand;
import br.com.nathanfiorito.finances.domain.transaction.enums.PaymentMethod;
import br.com.nathanfiorito.finances.domain.transaction.enums.TransactionType;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.UUID;

public record UpdateTransactionRequest(
    BigDecimal amount,
    LocalDate date,
    String establishment,
    String description,
    Integer categoryId,
    String paymentMethod,
    String transactionType
) {
    public UpdateTransactionCommand toCommand(UUID id) {
        return new UpdateTransactionCommand(
            id,
            amount,
            date,
            establishment,
            description,
            categoryId,
            paymentMethod != null ? PaymentMethod.valueOf(paymentMethod.toUpperCase()) : null,
            transactionType != null ? TransactionType.valueOf(transactionType.toUpperCase()) : null
        );
    }
}
