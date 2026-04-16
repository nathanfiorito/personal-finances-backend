package br.com.nathanfiorito.finances.domain.transaction.records;

import br.com.nathanfiorito.finances.domain.transaction.enums.PaymentMethod;
import br.com.nathanfiorito.finances.domain.transaction.enums.TransactionType;
import org.junit.jupiter.api.Test;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;

class TransactionTest {

    @Test
    void shouldCreateTransactionWithAllFields() {
        UUID id = UUID.randomUUID();
        var transaction = new Transaction(
            id, new BigDecimal("100.00"), LocalDate.of(2026, 1, 15),
            "Supermarket", "Weekly groceries", 1, "Alimentação",
            null, "text", TransactionType.EXPENSE, PaymentMethod.DEBIT,
            0.95, null, null, LocalDateTime.of(2026, 1, 15, 10, 0)
        );

        assertThat(transaction.id()).isEqualTo(id);
        assertThat(transaction.amount()).isEqualByComparingTo("100.00");
        assertThat(transaction.category()).isEqualTo("Alimentação");
        assertThat(transaction.transactionType()).isEqualTo(TransactionType.EXPENSE);
        assertThat(transaction.paymentMethod()).isEqualTo(PaymentMethod.DEBIT);
    }

    @Test
    void shouldSupportIncomeTransactionType() {
        var transaction = new Transaction(
            UUID.randomUUID(), new BigDecimal("5000.00"), LocalDate.now(),
            "Employer", null, 2, "Salário", null, "text",
            TransactionType.INCOME, PaymentMethod.CREDIT, 1.0, null, null, LocalDateTime.now()
        );

        assertThat(transaction.transactionType()).isEqualTo(TransactionType.INCOME);
        assertThat(transaction.paymentMethod()).isEqualTo(PaymentMethod.CREDIT);
    }

    @Test
    void shouldAllowNullableFields() {
        var transaction = new Transaction(
            UUID.randomUUID(), new BigDecimal("30.00"), LocalDate.now(),
            null, null, 1, "Transport", null, "text",
            TransactionType.EXPENSE, PaymentMethod.DEBIT, null, null, null, LocalDateTime.now()
        );

        assertThat(transaction.establishment()).isNull();
        assertThat(transaction.description()).isNull();
        assertThat(transaction.taxId()).isNull();
        assertThat(transaction.confidence()).isNull();
    }
}
