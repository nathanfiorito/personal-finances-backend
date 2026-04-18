# CLAUDE.md — db/migration/

## Purpose

Flyway migrations. The database schema lives here and only here. Hibernate runs in `ddl-auto=validate`, so any drift between an `@Entity` and the live schema fails startup.

## Rules

- **Every schema change is a new migration file.** Never edit an applied migration.
- **One concern per migration.** A migration adds a table, or a column, or an index — not all three.
- **File name:** `V<N>__<snake_description>.sql`, sequential integer version.
- **Entity changes require integration tests.** Any new or modified `@Entity` must ship with a Testcontainers-backed `*IT.java` in the same PR that exercises the full persistence path. See `../../../test/java/br/com/nathanfiorito/finances/CLAUDE.md`.

## Current migrations

| Version | File | Summary |
|---|---|---|
| V1 | `V1__init.sql` | Creates `categories` and `transactions` + indexes on transactions (date, category_id, (date, category_id), transaction_type) |
| V2 | `V2__confidence_to_double.sql` | `transactions.confidence` → `DOUBLE PRECISION` |
| V3 | `V3__create_credit_cards.sql` | Creates `credit_cards` (card metadata: name, brand, last4, closing/due day, active) |
| V4 | `V4__add_card_id_to_transactions.sql` | Adds nullable `transactions.card_id` FK → `credit_cards(id)` |
| V5 | `V5__create_invoice_predictions.sql` | Creates `invoice_predictions` (per card + period projection cache) |
| V6 | `V6__add_invoice_entry_type.sql` | Extends `transactions.entry_type` CHECK to include `invoice` (now `image|text|pdf|manual|invoice`) |

## Schema at a glance

- `categories(id SERIAL PK, name UNIQUE, active BOOL, created_at, updated_at)`
- `transactions(id UUID PK, amount DECIMAL(10,2), date, establishment, description, category_id FK, card_id FK NULL, tax_id, entry_type CHECK ∈ {image,text,pdf,manual,invoice}, transaction_type CHECK ∈ {EXPENSE,INCOME}, payment_method CHECK ∈ {CREDIT,DEBIT}, confidence DOUBLE PRECISION, created_at, updated_at)`
- `credit_cards(id SERIAL PK, name, brand, last4, closing_day, due_day, active, created_at, updated_at)`
- `invoice_predictions(id, card_id FK, period, projected_total, computed_at, ...)`

See the corresponding `.sql` file for exact column types, nullability, defaults, and check constraints.

## When to update this file

- New `V*.sql` → add the row to the Current migrations table and update Schema at a glance.
- Dropped table or column → strike through or remove the row; do not rewrite history.

## Pointers

- `@Entity` classes that must match these tables: `../../../main/java/.../infrastructure/*/entity/`.
- Integration test base + conventions: `../../../test/java/br/com/nathanfiorito/finances/CLAUDE.md`.
