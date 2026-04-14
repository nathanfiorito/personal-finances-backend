package br.com.nathanfiorito.finances.infrastructure.transaction.mapper;

import br.com.nathanfiorito.finances.domain.transaction.enums.PaymentMethod;
import br.com.nathanfiorito.finances.domain.transaction.enums.TransactionType;
import br.com.nathanfiorito.finances.domain.transaction.records.ExtractedTransaction;
import br.com.nathanfiorito.finances.domain.transaction.records.Transaction;
import br.com.nathanfiorito.finances.infrastructure.category.entity.CategoryEntity;
import br.com.nathanfiorito.finances.infrastructure.transaction.entity.TransactionEntity;
import org.junit.jupiter.api.Test;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;

class TransactionMapperTest {

    @Test
    void toDomainShouldMapAllFields() {
        CategoryEntity category = new CategoryEntity();
        category.setId(3);
        category.setName("Transport");

        TransactionEntity entity = new TransactionEntity();
        entity.setId(UUID.fromString("11111111-1111-1111-1111-111111111111"));
        entity.setAmount(new BigDecimal("99.99"));
        entity.setDate(LocalDate.of(2026, 1, 10));
        entity.setEstablishment("Gas Station");
        entity.setDescription("Fuel");
        entity.setCategory(category);
        entity.setTaxId("12.345.678/0001-99");
        entity.setEntryType("image");
        entity.setTransactionType(TransactionType.EXPENSE);
        entity.setPaymentMethod(PaymentMethod.CREDIT);
        entity.setConfidence(0.95);
        entity.setCreatedAt(LocalDateTime.of(2026, 1, 10, 12, 0));

        Transaction result = TransactionMapper.toDomain(entity);

        assertThat(result.id()).isEqualTo(UUID.fromString("11111111-1111-1111-1111-111111111111"));
        assertThat(result.amount()).isEqualByComparingTo("99.99");
        assertThat(result.date()).isEqualTo(LocalDate.of(2026, 1, 10));
        assertThat(result.establishment()).isEqualTo("Gas Station");
        assertThat(result.description()).isEqualTo("Fuel");
        assertThat(result.categoryId()).isEqualTo(3);
        assertThat(result.category()).isEqualTo("Transport");
        assertThat(result.taxId()).isEqualTo("12.345.678/0001-99");
        assertThat(result.entryType()).isEqualTo("image");
        assertThat(result.transactionType()).isEqualTo(TransactionType.EXPENSE);
        assertThat(result.paymentMethod()).isEqualTo(PaymentMethod.CREDIT);
        assertThat(result.confidence()).isEqualTo(0.95);
        assertThat(result.createdAt()).isEqualTo(LocalDateTime.of(2026, 1, 10, 12, 0));
    }

    @Test
    void toEntityShouldMapExtractedTransactionAndCategory() {
        CategoryEntity category = new CategoryEntity();
        category.setId(2);
        category.setName("Food");

        ExtractedTransaction extracted = new ExtractedTransaction(
            new BigDecimal("25.50"),
            LocalDate.of(2026, 2, 5),
            "Restaurant",
            "Lunch",
            null,
            "text",
            TransactionType.EXPENSE,
            PaymentMethod.DEBIT,
            0.88
        );

        TransactionEntity result = TransactionMapper.toEntity(extracted, category);

        assertThat(result.getAmount()).isEqualByComparingTo("25.50");
        assertThat(result.getDate()).isEqualTo(LocalDate.of(2026, 2, 5));
        assertThat(result.getEstablishment()).isEqualTo("Restaurant");
        assertThat(result.getDescription()).isEqualTo("Lunch");
        assertThat(result.getCategory()).isEqualTo(category);
        assertThat(result.getEntryType()).isEqualTo("text");
        assertThat(result.getTransactionType()).isEqualTo(TransactionType.EXPENSE);
        assertThat(result.getPaymentMethod()).isEqualTo(PaymentMethod.DEBIT);
        assertThat(result.getConfidence()).isEqualTo(0.88);
    }
}
