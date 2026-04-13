-- Migration: rename transaction_type value 'outcome' -> 'expense'
-- Safe to run multiple times (idempotent UPDATE + constraint re-creation)

BEGIN;

-- 1. Drop the existing CHECK constraint
ALTER TABLE transactions
    DROP CONSTRAINT IF EXISTS transactions_transaction_type_check;

-- 2. Rename existing 'outcome' rows to 'expense'
UPDATE transactions
SET transaction_type = 'expense'
WHERE transaction_type = 'outcome';

-- 3. Re-add CHECK constraint with the new allowed values
ALTER TABLE transactions
    ADD CONSTRAINT transactions_transaction_type_check
    CHECK (transaction_type IN ('income', 'expense'));

COMMIT;
