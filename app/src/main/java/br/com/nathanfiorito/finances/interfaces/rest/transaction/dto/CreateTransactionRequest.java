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
    String taxId,
    Integer cardId
) {
    public CreateTransactionCommand toCommand() {
        PaymentMethod resolvedPaymentMethod = PaymentMethod.valueOf(paymentMethod.toUpperCase());
        if (resolvedPaymentMethod == PaymentMethod.CREDIT && cardId == null) {
            throw new IllegalArgumentException("Card ID is required for credit card transactions");
        }
        if (resolvedPaymentMethod != PaymentMethod.CREDIT && cardId != null) {
            throw new IllegalArgumentException("Card ID must be null for non-credit transactions");
        }
        return new CreateTransactionCommand(
            amount,
            date != null ? date : LocalDate.now(),
            categoryId,
            entryType != null ? entryType : "manual",
            transactionType != null
                ? TransactionType.valueOf(transactionType.toUpperCase())
                : TransactionType.EXPENSE,
            resolvedPaymentMethod,
            establishment,
            description,
            taxId,
            1.0,
            cardId
        );
    }
}
