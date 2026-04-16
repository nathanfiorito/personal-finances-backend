ALTER TABLE transactions
    ADD COLUMN card_id INT REFERENCES credit_cards(id);

ALTER TABLE transactions
    ADD CONSTRAINT chk_card_id_credit
    CHECK (
        (payment_method = 'CREDIT' AND card_id IS NOT NULL)
        OR (payment_method != 'CREDIT' AND card_id IS NULL)
        OR (payment_method IS NULL AND card_id IS NULL)
    );

CREATE INDEX idx_transactions_card_id ON transactions (card_id);
