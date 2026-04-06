# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**FinBot** — personal Telegram bot for expense tracking. Receives payment receipts (photo, PDF, or free text), extracts and categorizes expenses using AI agents, and generates financial reports. Single-user, private use.

## Stack

- **Backend:** Python 3.12+ / FastAPI
- **Bot:** python-telegram-bot (webhook mode, not polling)
- **LLM:** Claude Sonnet 4.6 (vision + reports) and Haiku 4.5 (text extraction + categorization) via **OpenRouter** (OpenAI-compatible API, not direct Anthropic API)
- **Database:** Supabase (PostgreSQL)
- **Hosting:** Render (prod) + Cloudflare Tunnel (dev)
- **Scheduler:** APScheduler (monthly auto-reports)

## Commands

```bash
# Setup
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

# Run dev server
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

# Run tests
pytest tests/

# Run a single test file
pytest tests/test_extractor.py -v

# Expose local server via Cloudflare Tunnel (dev webhook)
cloudflared tunnel --url http://localhost:8000

# Register Telegram webhook
curl -X POST "https://api.telegram.org/bot<TOKEN>/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://<tunnel-url>/webhook", "secret_token": "<SECRET>"}'
```

## Architecture

Modular monolith. Entry point: `src/main.py` (FastAPI app + webhook setup).

### Request Flow

1. Telegram sends POST to `/webhook` → `handlers/message.py` or `handlers/commands.py`
2. Router in `handlers/` identifies input type (image/PDF/text/command)
3. `agents/extractor.py` → calls OpenRouter with Sonnet 4.6 (images) or Haiku 4.5 (text) → returns structured JSON
4. `agents/categorizer.py` → calls Haiku 4.5 → returns category
5. Bot sends confirmation via inline keyboard (`handlers/callback.py`)
6. On user confirmation → `services/database.py` persists to Supabase
7. `agents/reporter.py` handles `/relatorio` commands and monthly cron

### Key Design Decisions

- **OpenRouter, not Anthropic direct:** Use OpenAI-compatible SDK pointed at `openrouter.ai/api/v1`. Model IDs: `anthropic/claude-sonnet-4-6` and `anthropic/claude-haiku-4-5`.
- **Two models:** Sonnet 4.6 for image vision and report generation; Haiku 4.5 for categorization and plain-text extraction (cost optimization).
- **Mandatory confirmation:** Never persist an expense without explicit user confirmation via Telegram inline keyboard. Temporary state between extraction and confirmation must be held in memory (or a simple in-process dict keyed by `chat_id`).
- **Webhook + secret_token:** All requests to `/webhook` must be validated via `X-Telegram-Bot-Api-Secret-Token` header. Access is additionally restricted to a single `TELEGRAM_ALLOWED_CHAT_ID`.

### Database Schema (Supabase/PostgreSQL)

Main table: `expenses` — columns: `id` (UUID), `valor` (DECIMAL), `data` (DATE), `estabelecimento`, `descricao`, `categoria`, `cnpj`, `localizacao`, `tipo_entrada` (`'imagem'|'texto'|'pdf'`), `confianca` (0.00–1.00), `dados_raw` (JSONB), `created_at`, `updated_at`.

Indexes on `data`, `categoria`, and `(data, categoria)` for report queries.

### Default Categories

Alimentação, Transporte, Moradia, Saúde, Educação, Lazer, Vestuário, Serviços, Pets, Outros.

## Environment Variables

See `.env.example`. Key vars: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_WEBHOOK_SECRET`, `TELEGRAM_ALLOWED_CHAT_ID`, `OPENROUTER_API_KEY`, `SUPABASE_URL`, `SUPABASE_KEY`.
