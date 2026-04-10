-- FinBot: Current schema
-- To create the database from scratch, run this file in the Supabase SQL Editor.
--
-- Applied migrations history:
--   1. Initial schema (expenses table + categories)
--   2. FK expenses.category_id → categories.id; drop text category column
--   3. Rename expenses → transactions; add transaction_type
--   4. Rename Portuguese columns to English (migration_rename_columns.sql)
--
-- To update an existing database, apply migrations in order from docs/.

-- ============================================================
-- Categories
-- ============================================================

CREATE TABLE IF NOT EXISTS categories (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(100) UNIQUE NOT NULL,
    is_active   BOOLEAN DEFAULT TRUE,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE categories ENABLE ROW LEVEL SECURITY;

CREATE POLICY "service role full access"
    ON categories
    USING (true)
    WITH CHECK (true);

-- Seed: default categories
INSERT INTO categories (name) VALUES
    ('Alimentação'),
    ('Educação'),
    ('Lazer'),
    ('Moradia'),
    ('Outros'),
    ('Pets'),
    ('Saúde'),
    ('Serviços'),
    ('Transporte'),
    ('Vestuário')
ON CONFLICT (name) DO NOTHING;

-- ============================================================
-- Transactions
-- ============================================================

CREATE TABLE IF NOT EXISTS transactions (
    id                UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    amount            DECIMAL(10,2) NOT NULL,
    date              DATE NOT NULL,
    establishment     VARCHAR(255),
    description       TEXT,
    category_id       INT NOT NULL REFERENCES categories(id),
    tax_id            VARCHAR(18),
    entry_type        VARCHAR(20) NOT NULL CHECK (entry_type IN ('imagem', 'texto', 'pdf')),
    transaction_type  VARCHAR(10) NOT NULL DEFAULT 'outcome'
                          CHECK (transaction_type IN ('income', 'outcome')),
    confidence        DECIMAL(3,2) CHECK (confidence BETWEEN 0.00 AND 1.00),
    raw_data          JSONB DEFAULT '{}',
    created_at        TIMESTAMPTZ DEFAULT NOW(),
    updated_at        TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_transactions_date               ON transactions(date);
CREATE INDEX IF NOT EXISTS idx_transactions_category_id        ON transactions(category_id);
CREATE INDEX IF NOT EXISTS idx_transactions_date_category_id   ON transactions(date, category_id);
CREATE INDEX IF NOT EXISTS idx_transactions_transaction_type   ON transactions(transaction_type);

ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "service role full access"
    ON transactions
    USING (true)
    WITH CHECK (true);
