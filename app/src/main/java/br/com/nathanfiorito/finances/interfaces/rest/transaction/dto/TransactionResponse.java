package br.com.nathanfiorito.finances.interfaces.rest.transaction.dto;

import br.com.nathanfiorito.finances.domain.transaction.records.Transaction;

import java.util.UUID;

public record TransactionResponse(
    UUID id,
    String amount,
    String date,
    String establishment,
    String description,
    Integer categoryId,
    String category,
    String taxId,
    String entryType,
    String transactionType,
    String paymentMethod,
    Double confidence,
    Integer cardId,
    String cardAlias,
    String createdAt
) {
    public static TransactionResponse from(Transaction tx) {
        return new TransactionResponse(
            tx.id(),
            tx.amount().toPlainString(),
            tx.date() != null ? tx.date().toString() : null,
            tx.establishment(),
            tx.description(),
            tx.categoryId(),
            tx.category(),
            tx.taxId(),
            tx.entryType(),
            tx.transactionType() != null ? tx.transactionType().name().toLowerCase() : null,
            tx.paymentMethod() != null ? tx.paymentMethod().name().toLowerCase() : null,
            tx.confidence(),
            tx.cardId(),
            tx.cardAlias(),
            tx.createdAt() != null ? tx.createdAt().toString() : null
        );
    }
}
