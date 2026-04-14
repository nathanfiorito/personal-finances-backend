package br.com.nathanfiorito.finances.infrastructure.transaction.mapper;

import br.com.nathanfiorito.finances.domain.transaction.records.ExtractedTransaction;
import br.com.nathanfiorito.finances.domain.transaction.records.Transaction;
import br.com.nathanfiorito.finances.infrastructure.category.entity.CategoryEntity;
import br.com.nathanfiorito.finances.infrastructure.transaction.entity.TransactionEntity;

public class TransactionMapper {

    private TransactionMapper() {}

    public static Transaction toDomain(TransactionEntity entity) {
        return new Transaction(
            entity.getId(),
            entity.getAmount(),
            entity.getDate(),
            entity.getEstablishment(),
            entity.getDescription(),
            entity.getCategory().getId(),
            entity.getCategory().getName(),
            entity.getTaxId(),
            entity.getEntryType(),
            entity.getTransactionType(),
            entity.getPaymentMethod(),
            entity.getConfidence(),
            entity.getCreatedAt()
        );
    }

    public static TransactionEntity toEntity(ExtractedTransaction extracted, CategoryEntity category) {
        TransactionEntity entity = new TransactionEntity();
        entity.setAmount(extracted.amount());
        entity.setDate(extracted.date());
        entity.setEstablishment(extracted.establishment());
        entity.setDescription(extracted.description());
        entity.setCategory(category);
        entity.setTaxId(extracted.taxId());
        entity.setEntryType(extracted.entryType());
        entity.setTransactionType(extracted.transactionType());
        entity.setPaymentMethod(extracted.paymentMethod());
        entity.setConfidence(extracted.confidence());
        return entity;
    }
}
