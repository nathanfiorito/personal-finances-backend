CREATE TABLE invoice_predictions (
    id              SERIAL PRIMARY KEY,
    card_id         INT           NOT NULL REFERENCES credit_cards(id),
    invoice_month   DATE          NOT NULL,
    predicted_total DECIMAL(10,2) NOT NULL,
    prediction_data JSONB,
    generated_at    TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    created_at      TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_prediction_card_month UNIQUE (card_id, invoice_month)
);
