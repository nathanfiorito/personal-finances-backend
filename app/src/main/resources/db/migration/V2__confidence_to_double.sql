ALTER TABLE transactions
    ALTER COLUMN confidence TYPE DOUBLE PRECISION
    USING confidence::double precision;
