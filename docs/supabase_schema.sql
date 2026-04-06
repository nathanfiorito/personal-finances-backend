-- FinBot: Schema inicial
-- Rodar no SQL Editor do Supabase (Settings > SQL Editor)

CREATE TABLE IF NOT EXISTS expenses (
    id              UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    valor           DECIMAL(10,2) NOT NULL,
    data            DATE NOT NULL,
    estabelecimento VARCHAR(255),
    descricao       TEXT,
    categoria       VARCHAR(100) NOT NULL,
    cnpj            VARCHAR(18),
    localizacao     VARCHAR(255),
    tipo_entrada    VARCHAR(20) NOT NULL CHECK (tipo_entrada IN ('imagem', 'texto', 'pdf')),
    confianca       DECIMAL(3,2) CHECK (confianca BETWEEN 0.00 AND 1.00),
    dados_raw       JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_expenses_data           ON expenses(data);
CREATE INDEX IF NOT EXISTS idx_expenses_categoria      ON expenses(categoria);
CREATE INDEX IF NOT EXISTS idx_expenses_data_categoria ON expenses(data, categoria);

-- Row Level Security
ALTER TABLE expenses ENABLE ROW LEVEL SECURITY;

-- Política: service role tem acesso total (usado pelo backend via SUPABASE_SERVICE_KEY)
CREATE POLICY "service role full access"
    ON expenses
    USING (true)
    WITH CHECK (true);

-- ============================================================
-- Categorias
-- ============================================================

CREATE TABLE IF NOT EXISTS categories (
    id          SERIAL PRIMARY KEY,
    nome        VARCHAR(100) UNIQUE NOT NULL,
    ativo       BOOLEAN DEFAULT TRUE,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE categories ENABLE ROW LEVEL SECURITY;

CREATE POLICY "service role full access"
    ON categories
    USING (true)
    WITH CHECK (true);

-- Seed: categorias padrão
INSERT INTO categories (nome) VALUES
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
ON CONFLICT (nome) DO NOTHING;

-- ============================================================
-- Migration: FK expenses.categoria_id → categories.id
-- Run this AFTER the initial schema and seed above.
-- ============================================================

-- 1. Add nullable FK column
ALTER TABLE expenses ADD COLUMN IF NOT EXISTS categoria_id INT REFERENCES categories(id);

-- 2. Populate from existing text column (match by name)
UPDATE expenses
SET categoria_id = (
    SELECT id FROM categories WHERE nome = expenses.categoria
)
WHERE categoria_id IS NULL;

-- 3. Fallback: rows that didn't match any category → "Outros"
UPDATE expenses
SET categoria_id = (SELECT id FROM categories WHERE nome = 'Outros')
WHERE categoria_id IS NULL;

-- 4. Enforce NOT NULL now that all rows are filled
ALTER TABLE expenses ALTER COLUMN categoria_id SET NOT NULL;

-- 5. Index for join performance
CREATE INDEX IF NOT EXISTS idx_expenses_categoria_id ON expenses(categoria_id);

-- 6. Drop the old text column
ALTER TABLE expenses DROP COLUMN IF EXISTS categoria;
