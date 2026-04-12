# Architecture — Personal Finances

## Overview

Personal Finances is a personal Telegram bot for expense tracking. It receives payment receipts (photo, PDF, or plain text), extracts and categorizes expenses using AI, and persists the data for financial reporting. The backend is a Python/FastAPI application using a hexagonal (ports & adapters) architecture in `src/v2/`, with LLM inference via OpenRouter and persistence via Supabase (PostgreSQL).

## Hexagonal Architecture

The codebase follows the ports & adapters pattern. Dependency flow is strictly one-way:

```
Primary Adapters (BFF, Telegram) → Domain (Use Cases + Ports) ← Secondary Adapters (Supabase, OpenRouter, etc.)
```

| Layer | Location | Responsibility |
|---|---|---|
| Domain Entities | `src/v2/domain/entities/` | Pure data types — `Expense`, `Category` |
| Domain Exceptions | `src/v2/domain/exceptions.py` | `ExpenseNotFoundError`, etc. |
| Domain Ports | `src/v2/domain/ports/` | Abstract interfaces for all external dependencies |
| Domain Use Cases | `src/v2/domain/use_cases/` | All business logic — no framework or DB imports |
| Secondary Adapters | `src/v2/adapters/secondary/` | Supabase repos, OpenRouter LLM, Telegram notifier, in-memory pending state |
| Primary Adapters | `src/v2/adapters/primary/` | BFF REST router (`/api/v2/...`) + Telegram webhook handler |
| Bootstrap | `src/v2/bootstrap.py` | Wires all adapters into use cases; builds the FastAPI router |

Architecture contracts are enforced at test time by `import-linter` (see `tests/v2/test_architecture.py`):
- Domain never imports from adapters
- Secondary adapters never import from primary adapters
- Entities and ports never import from use cases

## Package Layout

```
src/
├── config/settings.py          — Pydantic settings (env vars)
├── main.py                     — FastAPI app + lifespan + webhook endpoint
├── scheduler/reports.py        — APScheduler: monthly auto-report (1st of month, 08:00 BRT)
└── services/
    ├── llm.py                  — OpenRouter HTTP client with retry + tracing
    ├── telegram.py             — Telegram Bot API helpers (send_message, get_file, etc.)
    └── tracing.py              — OpenTelemetry span helpers

src/v2/
├── bootstrap.py                — Builds UseCaseContainer + FastAPI router
├── domain/
│   ├── entities/               — Expense, Category (dataclasses)
│   ├── exceptions.py           — Domain error types
│   ├── ports/                  — ABC interfaces: ExpenseRepository, LLMPort, NotifierPort, etc.
│   └── use_cases/
│       ├── expenses/           — CreateExpense, ListExpenses, GetExpense, UpdateExpense, DeleteExpense
│       ├── categories/         — ListCategories, CreateCategory, UpdateCategory, DeactivateCategory
│       ├── reports/            — GetSummary, GetMonthly, ExportCsv
│       └── telegram/           — ProcessMessage, ConfirmExpense, CancelExpense, ChangeCategory, GenerateTelegramReport
└── adapters/
    ├── primary/
    │   ├── bff/                — REST API (/api/v2/...) with JWT auth via Supabase
    │   └── telegram/           — Webhook router → message/command/callback handlers
    └── secondary/
        ├── supabase/           — SupabaseExpenseRepository, SupabaseCategoryRepository
        ├── openrouter/         — OpenRouterLLMAdapter (chat_completion via src/services/llm.py)
        ├── telegram_api/       — TelegramNotifierAdapter (wraps src/services/telegram.py)
        └── memory/             — InMemoryPendingStateAdapter (TTL-based pending expense store)
```

## Key Architectural Decisions

### ADR-001 — Hexagonal Architecture

- **Status:** Accepted
- **Context:** The original modular monolith had handler → agent → service → database coupling that made the domain logic impossible to test in isolation.
- **Decision:** Adopt ports & adapters in `src/v2/`. Domain use cases depend only on ABCs; adapters implement them.
- **Consequences:** All use cases are unit-testable with mocks. Import-linter enforces the contracts at CI time. Swapping Supabase or OpenRouter requires only a new secondary adapter.

### ADR-002 — OpenRouter as LLM Gateway

- **Status:** Accepted
- **Context:** Need to access multiple Claude models (Sonnet for vision, Haiku for classification) with unified billing.
- **Decision:** Use OpenRouter instead of the Anthropic API directly.
- **Consequences:** OpenAI-compatible SDK, model switching via a single parameter, centralized billing. Trade-off: 5.5% fee on credit purchases, dependency on an intermediary.

### ADR-003 — Webhook + Cloudflare Tunnel

- **Status:** Accepted
- **Context:** Webhook is more efficient than polling, but requires public HTTPS.
- **Decision:** Cloudflare Tunnel for dev; Cloudflare DNS + proxy in production (Render).
- **Consequences:** No polling overhead, free DDoS protection. Requires one-time tunnel setup.

### ADR-004 — Mandatory Confirmation Before Persisting

- **Status:** Accepted
- **Context:** LLMs can mis-extract data, especially from non-standard receipt layouts.
- **Decision:** Always show extracted data + category via inline keyboard; persist only after explicit confirmation.
- **Consequences:** Zero false positives in the database. Pending state held in-memory with TTL (10 min) in `InMemoryPendingStateAdapter`.

### ADR-005 — Supabase for Persistence

- **Status:** Accepted
- **Context:** Need managed PostgreSQL with a generous free tier.
- **Decision:** Supabase (free tier: 500 MB DB, REST API included).
- **Consequences:** Zero DB administration, Python SDK available. Trade-off: free projects pause after 7 days of inactivity (mitigated by daily bot usage).

### ADR-006 — Two LLM Models (Sonnet + Haiku)

- **Status:** Accepted
- **Context:** Image extraction requires a high-quality vision model; categorization is a simple classification task.
- **Decision:** Sonnet 4.6 for image extraction and reports; Haiku 4.5 for text extraction, categorization, duplicate checking.
- **Consequences:** Optimized cost (~$0.84/month for 100 expenses), lower latency for simple operations. Two API calls per image expense.

### ADR-007 — Duplicate Detection via LLM (Fail-Open)

- **Status:** Accepted
- **Context:** Users may accidentally send the same receipt twice. Deterministic comparison generates too many false negatives.
- **Decision:** Haiku 4.5 compares the new expense against the 3 most recent; DUPLICATE/OK response. On LLM failure, proceed with save (fail-open).
- **Consequences:** Context-aware duplicate detection. Trade-off: additional cost and latency during confirmation.

## Infrastructure

```
┌─────────────────────────────────────────────────────┐
│                    Cloudflare                        │
│              (DNS + Proxy + DDoS)                    │
│                                                     │
│   Dev: Cloudflare Tunnel ──► localhost:8000          │
│   Prod: DNS ──► Render (personal-finances.onrender.com) │
└──────────────────────┬──────────────────────────────┘
                       │ HTTPS
                       ▼
              ┌────────────────┐
              │  Render (Free) │
              │  FastAPI App   │
              └───────┬────────┘
                      │
           ┌──────────┼──────────┐
           ▼          ▼          ▼
      OpenRouter   Supabase   Telegram API
      (LLM API)   (PostgreSQL) (Bot API)
```

## Core Flows

### Flow 1 — Expense Registration (Image)

1. User sends a receipt photo in Telegram
2. Webhook receives the message, downloads the image via Telegram API (`get_file`)
3. `ProcessMessage` use case: sends image to LLM (`extract_expense`) → structured JSON
4. LLM also classifies the category; bot shows confirmation with inline keyboard
5. User confirms (or changes category) → `ConfirmExpense` use case
6. Duplicate check via `LLMPort.check_duplicate` against 3 most recent expenses
7. If no duplicate (or override): `ExpenseRepository.save()` persists to Supabase

### Flow 2 — Expense Registration (Text)

1. User sends: "gastei 120 no posto shell"
2. `ProcessMessage` use case: sends text to LLM (`extract_expense`) → structured JSON
3. Same confirmation + duplicate check + save flow as Flow 1

### Flow 3 — Expense Registration (PDF)

1. User sends a PDF (NF-e, receipt)
2. Size check: reject if > 10 MB
3. `pdfplumber` tries text extraction
   - If text ≥ 50 chars: process as text via Haiku 4.5
   - If scanned PDF: convert first page to JPEG via PyMuPDF → process as image via Sonnet 4.6
4. Same confirmation + save flow

### Flow 4 — On-Demand Report

1. User sends `/relatorio [semana|mes|anterior|MM/AAAA]`
2. `GenerateTelegramReport` use case: queries expenses for the period
3. Aggregates by category, calls LLM for a 2-sentence financial insight
4. Bot replies with category breakdown (emojis + percentages) + LLM insight

### Flow 5 — CSV Export

1. User sends `/exportar [semana|mes|anterior|MM/AAAA]`
2. `ExportCsv` use case: queries expenses, generates UTF-8 BOM CSV
3. Bot sends the file via Telegram with a caption showing count and period

### Flow 6 — Auto Monthly Report

1. APScheduler fires on the 1st of each month at 08:00 BRT
2. `send_monthly_report()` calls `GenerateTelegramReport` for the previous month
3. Bot proactively sends the report to the user

## Database Schema

See `docs/supabase_schema.sql` for the full schema.

```sql
-- Main expenses table
CREATE TABLE transactions (
    id               UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    amount           DECIMAL(10,2) NOT NULL,
    date             DATE NOT NULL,
    establishment    VARCHAR(255),
    description      TEXT,
    category_id      INT NOT NULL REFERENCES categories(id),
    tax_id           VARCHAR(18),
    entry_type       VARCHAR(20) NOT NULL CHECK (entry_type IN ('image', 'text', 'pdf')),
    transaction_type VARCHAR(20) NOT NULL DEFAULT 'expense',
    confidence       DECIMAL(3,2) CHECK (confidence BETWEEN 0.00 AND 1.00),
    raw_data         JSONB DEFAULT '{}',
    created_at       TIMESTAMPTZ DEFAULT NOW(),
    updated_at       TIMESTAMPTZ DEFAULT NOW()
);

-- Report query indexes
CREATE INDEX idx_transactions_date          ON transactions(date);
CREATE INDEX idx_transactions_category_id   ON transactions(category_id);
CREATE INDEX idx_transactions_date_category ON transactions(date, category_id);

-- Categories table
CREATE TABLE categories (
    id         SERIAL PRIMARY KEY,
    name       VARCHAR(100) UNIQUE NOT NULL,
    is_active  BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Default categories (seed):** Alimentação, Educação, Lazer, Moradia, Outros, Pets, Saúde, Serviços, Transporte, Vestuário.

## Security

- Webhook protected by Telegram `secret_token` (`X-Telegram-Bot-Api-Secret-Token` header)
- Access restricted by `chat_id` — single user, `TELEGRAM_ALLOWED_CHAT_ID`
- Rate limiting: 30 req/min on webhook, 60 req/min global (slowapi)
- REST API protected by Supabase JWT (`Authorization: Bearer <token>`)
- API keys in environment variables — never in code
- Financial data is not logged in plain text
- Cloudflare proxy hides the real server IP
- See `SECURITY-CHECKLIST.md` for full checklist

## Observability

When `SIGNOZ_OTLP_ENDPOINT` is set, the app exports:
- **Traces:** all HTTP requests + Supabase queries + LLM calls (via `_FilteringSpanProcessor` that drops noisy ASGI response-chunk spans)
- **Logs:** INFO+ logs forwarded to SigNoz via OTLP

HTTPX is auto-instrumented; spans are renamed to include the service name and path for readability (e.g. `supabase GET /rest/v1/transactions`).
