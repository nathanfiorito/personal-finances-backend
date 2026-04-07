-- Migration: rename expenses → transactions and add transaction_type
-- Run this against your Supabase project via the SQL editor or CLI.

-- Step 1: Rename the table
ALTER TABLE expenses RENAME TO transactions;

-- Step 2: Add transaction_type column (defaults all existing records to 'outcome')
ALTER TABLE transactions
  ADD COLUMN transaction_type VARCHAR NOT NULL DEFAULT 'outcome'
  CHECK (transaction_type IN ('income', 'outcome'));

-- Step 3: (Optional) Rename existing indexes that reference the old table name
-- Supabase usually renames them automatically, but if not:
-- ALTER INDEX expenses_data_idx RENAME TO transactions_data_idx;
-- ALTER INDEX expenses_categoria_id_idx RENAME TO transactions_categoria_id_idx;
