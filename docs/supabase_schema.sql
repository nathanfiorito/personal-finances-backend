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
