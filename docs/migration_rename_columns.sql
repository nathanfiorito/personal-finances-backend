-- Migration: rename Portuguese columns to English
-- Applies to: categories and transactions tables
-- Run this against your Supabase project via the SQL editor or CLI.
--
-- Column mapping:
--   categories:  nome → name,  ativo → is_active
--   transactions: valor → amount,  estabelecimento → establishment,
--     descricao → description,  categoria_id → category_id,  cnpj → tax_id,
--     tipo_entrada → entry_type,  confianca → confidence,  dados_raw → raw_data

-- ============================================================
-- categories table
-- ============================================================

ALTER TABLE categories RENAME COLUMN nome TO name;
ALTER TABLE categories RENAME COLUMN ativo TO is_active;

-- ============================================================
-- transactions table
-- ============================================================

ALTER TABLE transactions RENAME COLUMN valor TO amount;
ALTER TABLE transactions RENAME COLUMN estabelecimento TO establishment;
ALTER TABLE transactions RENAME COLUMN descricao TO description;
ALTER TABLE transactions RENAME COLUMN categoria_id TO category_id;
ALTER TABLE transactions RENAME COLUMN cnpj TO tax_id;
ALTER TABLE transactions RENAME COLUMN tipo_entrada TO entry_type;
ALTER TABLE transactions RENAME COLUMN confianca TO confidence;
ALTER TABLE transactions RENAME COLUMN dados_raw TO raw_data;

-- ============================================================
-- Rename indexes that referenced old column names
-- ============================================================

-- Drop old indexes (they will be recreated below with new names)
DROP INDEX IF EXISTS idx_transactions_categoria_id;
DROP INDEX IF EXISTS idx_transactions_data_categoria_id;

-- Recreate indexes with English column names
CREATE INDEX IF NOT EXISTS idx_transactions_category_id ON transactions(category_id);
CREATE INDEX IF NOT EXISTS idx_transactions_data_category_id ON transactions(date, category_id);

-- data index and transaction_type index keep their names (column names unchanged or English already)
-- idx_transactions_data → references "date" column (unchanged name)
-- idx_transactions_transaction_type → already English

-- ============================================================
-- Update RLS policy name (if it referenced Portuguese columns)
-- ============================================================
-- RLS policies use expressions, not column names directly in the policy name,
-- so no change needed here unless you want to rename the policy itself.

-- ============================================================
-- Verify
-- ============================================================
-- SELECT column_name, data_type FROM information_schema.columns
-- WHERE table_name = 'categories' ORDER BY ordinal_position;
--
-- SELECT column_name, data_type FROM information_schema.columns
-- WHERE table_name = 'transactions' ORDER BY ordinal_position;
