package br.com.nathanfiorito.finances.domain.transaction.enums;

import org.junit.jupiter.api.Test;
import static org.assertj.core.api.Assertions.assertThat;

class TransactionTypeTest {

    @Test
    void shouldHaveExpenseAndIncomeValues() {
        assertThat(TransactionType.values()).hasSize(2);
        assertThat(TransactionType.EXPENSE).isNotNull();
        assertThat(TransactionType.INCOME).isNotNull();
    }

    @Test
    void shouldResolveFromString() {
        assertThat(TransactionType.valueOf("EXPENSE")).isEqualTo(TransactionType.EXPENSE);
        assertThat(TransactionType.valueOf("INCOME")).isEqualTo(TransactionType.INCOME);
    }
}
