CREATE TABLE categories (
    id         SERIAL PRIMARY KEY,
    name       VARCHAR(100) NOT NULL UNIQUE,
    active     BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP    NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP    NOT NULL DEFAULT NOW()
);

CREATE TABLE transactions (
    id               UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
    amount           DECIMAL(10,2) NOT NULL,
    date             DATE          NOT NULL,
    establishment    VARCHAR(255),
    description      VARCHAR(500),
    category_id      INT           NOT NULL REFERENCES categories(id),
    tax_id           VARCHAR(20),
    entry_type       VARCHAR(10)   NOT NULL,
    transaction_type VARCHAR(10)   NOT NULL,
    payment_method   VARCHAR(10),
    confidence       DECIMAL(4,2),
    created_at       TIMESTAMP     NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMP     NOT NULL DEFAULT NOW()
);
