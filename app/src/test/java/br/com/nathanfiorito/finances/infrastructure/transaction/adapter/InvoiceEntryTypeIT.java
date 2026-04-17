package br.com.nathanfiorito.finances.infrastructure.transaction.adapter;

import br.com.nathanfiorito.finances.infrastructure.BaseRepositoryIT;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.jdbc.core.JdbcTemplate;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class InvoiceEntryTypeIT extends BaseRepositoryIT {

    @Autowired
    private JdbcTemplate jdbc;

    @Test
    void allowsInvoiceEntryType() {
        Integer catId = jdbc.queryForObject(
            "INSERT INTO categories(name, active) VALUES ('TestCat-invoice', TRUE) RETURNING id",
            Integer.class);

        jdbc.update("""
            INSERT INTO transactions (
                id, amount, date, establishment, category_id,
                entry_type, transaction_type, payment_method, card_id
            ) VALUES (
                gen_random_uuid(), 10.00, CURRENT_DATE, 'X', ?,
                'invoice', 'EXPENSE', NULL, NULL
            )
            """, catId);

        Integer count = jdbc.queryForObject(
            "SELECT COUNT(*) FROM transactions WHERE entry_type = 'invoice'",
            Integer.class);
        assertThat(count).isEqualTo(1);
    }

    @Test
    void rejectsUnknownEntryType() {
        Integer catId = jdbc.queryForObject(
            "INSERT INTO categories(name, active) VALUES ('TestCat-bogus', TRUE) RETURNING id",
            Integer.class);

        assertThatThrownBy(() -> jdbc.update("""
            INSERT INTO transactions (
                id, amount, date, establishment, category_id,
                entry_type, transaction_type, payment_method, card_id
            ) VALUES (
                gen_random_uuid(), 10.00, CURRENT_DATE, 'X', ?,
                'bogus', 'EXPENSE', NULL, NULL
            )
            """, catId))
            .hasMessageContaining("transactions_entry_type_check");
    }
}
