CREATE TABLE categories (
    id         SERIAL PRIMARY KEY,
    name       VARCHAR(100) NOT NULL UNIQUE,
    active     BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE TABLE transactions (
    id               UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
    amount           DECIMAL(10,2) NOT NULL,
    date             DATE          NOT NULL,
    establishment    VARCHAR(255),
    description      VARCHAR(500),
    category_id      INT           NOT NULL REFERENCES categories(id),
    tax_id           VARCHAR(20),
    entry_type       VARCHAR(20)   NOT NULL CHECK (entry_type IN ('image', 'text', 'pdf', 'manual')),
    transaction_type VARCHAR(10)   NOT NULL CHECK (transaction_type IN ('EXPENSE', 'INCOME')),
    payment_method   VARCHAR(10)            CHECK (payment_method IN ('CREDIT', 'DEBIT')),
    confidence       DECIMAL(4,2),
    created_at       TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_transactions_date              ON transactions (date);
CREATE INDEX idx_transactions_category_id       ON transactions (category_id);
CREATE INDEX idx_transactions_date_category_id  ON transactions (date, category_id);
CREATE INDEX idx_transactions_transaction_type  ON transactions (transaction_type);
