ALTER TABLE transactions DROP CONSTRAINT transactions_entry_type_check;

ALTER TABLE transactions ADD CONSTRAINT transactions_entry_type_check
    CHECK (entry_type IN ('image', 'text', 'pdf', 'manual', 'invoice'));
