# CLAUDE.md — personal-finances-backend

This file provides guidance to Claude Code when working in this repository.

**Always read `docs/patterns.md`, `docs/workflows.md`, and `docs/rules.md` before making changes.**

## Project Overview

Personal Telegram bot for expense tracking. Receives payment receipts (photo, PDF, or free text), extracts and categorizes expenses using AI, and exposes a REST API for the frontend. Single-user, private use.

## Stack

- **Backend:** Python 3.12+ / FastAPI, hexagonal (ports & adapters) architecture in `src/v2/`
- **Bot:** httpx (direct HTTP calls to Telegram Bot API, webhook mode, not polling)
- **LLM:** Claude Sonnet 4.6 (vision + reports) and Haiku 4.5 (text extraction + categorization + duplicate check) via **OpenRouter** (OpenAI-compatible API, not Anthropic direct)
- **Database:** Supabase (PostgreSQL)
- **Hosting:** Render (prod) + Cloudflare Tunnel (dev)
- **Scheduler:** APScheduler (monthly auto-reports)
- **Testing:** pytest + pytest-asyncio; architecture enforced by import-linter

## Commands

```bash
# Setup
python -m venv .venv
source .venv/Scripts/activate   # Windows: Scripts; Linux/Mac: bin
pip install -r requirements.txt
cp .env.example .env

# Run dev server (set ENVIRONMENT=development in .env to expose /openapi.json)
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

# Run tests
pytest tests/

# Run a single test file
pytest tests/test_webhook.py -v

# Lint
ruff check src/

# Expose local server via Cloudflare Tunnel (dev webhook)
cloudflared tunnel --url http://localhost:8000
```

## Architecture

Hexagonal (ports & adapters). Entry point: `src/main.py`.

### Package layout

```
src/
├── config/settings.py       — Pydantic settings (env vars)
├── main.py                  — FastAPI app + lifespan + /webhook
├── scheduler/reports.py     — APScheduler monthly auto-report
└── services/
    ├── llm.py               — OpenRouter HTTP client (retry + tracing)
    ├── telegram.py          — Telegram Bot API helpers
    └── tracing.py           — OpenTelemetry span helpers

src/v2/                      — Hexagonal architecture
├── bootstrap.py             — Wires adapters → use cases; builds FastAPI router
├── domain/
│   ├── entities/            — Expense, Category (dataclasses, no framework imports)
│   ├── exceptions.py        — Domain error types
│   ├── ports/               — ABC interfaces (ExpenseRepository, LLMPort, etc.)
│   └── use_cases/           — All business logic (expenses/, categories/, reports/, telegram/)
└── adapters/
    ├── primary/
    │   ├── bff/             — REST API (/api/v2/...) with JWT auth
    │   └── telegram/        — Webhook router + message/command/callback handlers
    └── secondary/
        ├── supabase/        — Supabase expense + category repositories
        ├── openrouter/      — OpenRouter LLM adapter
        ├── telegram_api/    — Telegram notifier adapter
        └── memory/          — In-memory pending state (TTL 10 min)
```

Architecture contracts are enforced by import-linter (see `tests/v2/test_architecture.py`):
- Domain never imports from adapters
- Secondary adapters never import from primary adapters
- Entities/ports never import from use cases

### Request flow (Telegram bot)

1. POST to `/webhook` → v2 webhook handler (`src/v2/adapters/primary/telegram/webhook.py`)
2. Routes to `handle_message`, `handle_command`, or `handle_callback`
3. `ProcessMessage` use case: calls `LLMPort.extract_expense()` → structured data
4. Bot sends confirmation via Telegram inline keyboard
5. On confirmation: `ConfirmExpense` use case → `LLMPort.check_duplicate()` → `ExpenseRepository.save()`

### REST API

Routes at `/api/v2/...`, all protected by Supabase JWT:
- `GET/POST /api/v2/transactions`, `GET/PUT/DELETE /api/v2/transactions/{id}`
- `GET/POST /api/v2/categories`, `PATCH/DELETE /api/v2/categories/{id}`
- `GET /api/v2/reports/summary`, `GET /api/v2/reports/monthly`
- `GET /api/v2/export/csv`

### Key design decisions

- **OpenRouter, not Anthropic direct:** Use OpenAI-compatible SDK at `openrouter.ai/api/v1`. Model IDs: `anthropic/claude-sonnet-4-6` and `anthropic/claude-haiku-4-5`.
- **Two models:** Sonnet 4.6 for image vision and reports; Haiku 4.5 for text extraction, categorization, duplicate checking (cost optimization).
- **Mandatory confirmation:** Never persist without explicit user confirmation. Pending state held in `InMemoryPendingStateAdapter` (TTL 10 min).
- **Webhook security:** Validate `X-Telegram-Bot-Api-Secret-Token` header; restrict to single `TELEGRAM_ALLOWED_CHAT_ID`.
- **OpenAPI hidden in production:** `openapi_url=None` when `ENVIRONMENT=production` (default). Set `ENVIRONMENT=development` to expose `/openapi.json`.

### Bot commands

| Command | Description |
|---|---|
| `/start` | Welcome message |
| `/ajuda` | List all commands |
| `/relatorio [semana\|anterior\|mes\|MM/AAAA]` | Expense report for a period |
| `/exportar [semana\|anterior\|mes\|MM/AAAA]` | Export expenses as CSV |
| `/categorias` | List active categories |
| `/categorias add <name>` | Add a new category |

### Database schema

**Table `transactions`** — `id` (UUID), `amount` (DECIMAL), `date` (DATE), `establishment`, `description`, `category_id` (INT FK), `tax_id`, `entry_type` (`'image'|'text'|'pdf'`), `transaction_type` (`'expense'|'income'`), `payment_method` (`'credit'|'debit'`), `confidence` (0.00–1.00), `raw_data` (JSONB), `created_at`, `updated_at`.

**Table `categories`** — `id` (SERIAL), `name` (VARCHAR UNIQUE), `is_active` (BOOLEAN), `created_at`.

## Environment Variables

See `.env.example`. Key vars: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_WEBHOOK_SECRET`, `TELEGRAM_ALLOWED_CHAT_ID`, `OPENROUTER_API_KEY`, `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `ENVIRONMENT` (default: `production`).
