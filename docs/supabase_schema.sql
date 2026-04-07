-- FinBot: Schema atual
-- Estado reflete todas as migrations aplicadas até agora.
-- Para criar o banco do zero, execute este arquivo no SQL Editor do Supabase.
--
-- Histórico de migrations aplicadas:
--   1. Schema inicial (tabela expenses + categorias)
--   2. FK expenses.categoria_id → categories.id; drop coluna texto categoria
--   3. Rename expenses → transactions; add transaction_type
--
-- Para atualizar um banco existente, use os arquivos em docs/:
--   - migration_transactions.sql

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
-- Transactions
-- ============================================================

CREATE TABLE IF NOT EXISTS transactions (
    id              UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    valor           DECIMAL(10,2) NOT NULL,
    data            DATE NOT NULL,
    estabelecimento VARCHAR(255),
    descricao       TEXT,
    categoria_id    INT NOT NULL REFERENCES categories(id),
    cnpj            VARCHAR(18),
    tipo_entrada    VARCHAR(20) NOT NULL CHECK (tipo_entrada IN ('imagem', 'texto', 'pdf')),
    transaction_type VARCHAR(10) NOT NULL DEFAULT 'outcome'
                        CHECK (transaction_type IN ('income', 'outcome')),
    confianca       DECIMAL(3,2) CHECK (confianca BETWEEN 0.00 AND 1.00),
    dados_raw       JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_transactions_data              ON transactions(data);
CREATE INDEX IF NOT EXISTS idx_transactions_categoria_id      ON transactions(categoria_id);
CREATE INDEX IF NOT EXISTS idx_transactions_data_categoria_id ON transactions(data, categoria_id);
CREATE INDEX IF NOT EXISTS idx_transactions_transaction_type  ON transactions(transaction_type);

ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "service role full access"
    ON transactions
    USING (true)
    WITH CHECK (true);
