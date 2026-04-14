package br.com.nathanfiorito.finances.interfaces.rest.transaction.dto;

import br.com.nathanfiorito.finances.application.transaction.commands.CreateTransactionCommand;
import br.com.nathanfiorito.finances.domain.transaction.enums.PaymentMethod;
import br.com.nathanfiorito.finances.domain.transaction.enums.TransactionType;
import jakarta.validation.constraints.DecimalMax;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Positive;

import java.math.BigDecimal;
import java.time.LocalDate;

public record CreateTransactionRequest(
    @NotNull(message = "Amount is required")
    @Positive(message = "Amount must be positive")
    @DecimalMax(value = "999999.99", message = "Amount must not exceed 999999.99")
    BigDecimal amount,

    @NotNull(message = "Category is required")
    Integer categoryId,

    @NotNull(message = "Payment method is required")
    String paymentMethod,

    LocalDate date,
    String transactionType,
    String entryType,
    String establishment,
    String description,
    String taxId
) {
    public CreateTransactionCommand toCommand() {
        return new CreateTransactionCommand(
            amount,
            date != null ? date : LocalDate.now(),
            categoryId,
            entryType != null ? entryType : "manual",
            transactionType != null
                ? TransactionType.valueOf(transactionType.toUpperCase())
                : TransactionType.EXPENSE,
            PaymentMethod.valueOf(paymentMethod.toUpperCase()),
            establishment,
            description,
            taxId,
            1.0
        );
    }
}
