package br.com.nathanfiorito.finances.domain.transaction.records;

import br.com.nathanfiorito.finances.domain.transaction.enums.PaymentMethod;
import br.com.nathanfiorito.finances.domain.transaction.enums.TransactionType;
import org.junit.jupiter.api.Test;

import java.math.BigDecimal;
import java.time.LocalDate;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class ExtractedTransactionTest {

    private ExtractedTransaction validExtracted() {
        return new ExtractedTransaction(
            new BigDecimal("50.00"), LocalDate.of(2026, 1, 15),
            "Test Store", null, null, "text",
            TransactionType.EXPENSE, PaymentMethod.DEBIT, 0.9
        );
    }

    @Test
    void shouldCreateValidExtractedTransaction() {
        var extracted = validExtracted();
        assertThat(extracted.amount()).isEqualByComparingTo("50.00");
        assertThat(extracted.transactionType()).isEqualTo(TransactionType.EXPENSE);
        assertThat(extracted.confidence()).isEqualTo(0.9);
    }

    @Test
    void shouldThrowWhenAmountIsZero() {
        assertThatThrownBy(() -> new ExtractedTransaction(
            BigDecimal.ZERO, null, null, null, null, "text",
            TransactionType.EXPENSE, PaymentMethod.DEBIT, 0.5
        )).isInstanceOf(IllegalArgumentException.class)
          .hasMessageContaining("positive");
    }

    @Test
    void shouldThrowWhenAmountIsNegative() {
        assertThatThrownBy(() -> new ExtractedTransaction(
            new BigDecimal("-1.00"), null, null, null, null, "text",
            TransactionType.EXPENSE, PaymentMethod.DEBIT, 0.5
        )).isInstanceOf(IllegalArgumentException.class)
          .hasMessageContaining("positive");
    }

    @Test
    void shouldThrowWhenAmountExceedsLimit() {
        assertThatThrownBy(() -> new ExtractedTransaction(
            new BigDecimal("1000000.00"), null, null, null, null, "text",
            TransactionType.EXPENSE, PaymentMethod.DEBIT, 0.5
        )).isInstanceOf(IllegalArgumentException.class)
          .hasMessageContaining("limit");
    }

    @Test
    void shouldFormatCnpjTaxId() {
        var extracted = new ExtractedTransaction(
            new BigDecimal("50.00"), null, null, null, "12345678000195",
            "text", TransactionType.EXPENSE, PaymentMethod.DEBIT, 0.5
        );
        assertThat(extracted.taxId()).isEqualTo("12.345.678/0001-95");
    }

    @Test
    void shouldLeaveNonCnpjTaxIdUnchanged() {
        var extracted = new ExtractedTransaction(
            new BigDecimal("50.00"), null, null, null, "123",
            "text", TransactionType.EXPENSE, PaymentMethod.DEBIT, 0.5
        );
        assertThat(extracted.taxId()).isEqualTo("123");
    }

    @Test
    void shouldLeaveNullTaxIdAsNull() {
        var extracted = validExtracted();
        assertThat(extracted.taxId()).isNull();
    }
}
