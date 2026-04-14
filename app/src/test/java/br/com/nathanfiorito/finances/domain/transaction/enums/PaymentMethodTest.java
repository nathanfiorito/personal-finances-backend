package br.com.nathanfiorito.finances.domain.transaction.enums;

import org.junit.jupiter.api.Test;
import static org.assertj.core.api.Assertions.assertThat;

class PaymentMethodTest {

    @Test
    void shouldHaveCreditAndDebitValues() {
        assertThat(PaymentMethod.values()).hasSize(2);
        assertThat(PaymentMethod.CREDIT).isNotNull();
        assertThat(PaymentMethod.DEBIT).isNotNull();
    }

    @Test
    void shouldResolveFromString() {
        assertThat(PaymentMethod.valueOf("CREDIT")).isEqualTo(PaymentMethod.CREDIT);
        assertThat(PaymentMethod.valueOf("DEBIT")).isEqualTo(PaymentMethod.DEBIT);
    }
}
