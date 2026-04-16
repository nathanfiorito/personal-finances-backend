CREATE TABLE credit_cards (
    id              SERIAL PRIMARY KEY,
    alias           VARCHAR(100)  NOT NULL,
    bank            VARCHAR(100)  NOT NULL,
    last_four_digits CHAR(4)      NOT NULL,
    closing_day     SMALLINT      NOT NULL CHECK (closing_day BETWEEN 1 AND 31),
    due_day         SMALLINT      NOT NULL CHECK (due_day BETWEEN 1 AND 31),
    active          BOOLEAN       NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_credit_cards_active ON credit_cards (active);
