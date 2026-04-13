# personal-finances-backend

FastAPI backend and Telegram bot for personal expense tracking. Receives payment receipts (photo, PDF, or text), extracts and categorizes expenses using AI agents, and exposes a REST API for the frontend.

## Stack

| Component | Technology |
|---|---|
| Runtime | Python 3.12+ / FastAPI |
| Bot | httpx (Telegram Bot API, webhook mode) |
| LLM | Claude Sonnet 4.6 + Haiku 4.5 via OpenRouter |
| Database | PostgreSQL (Supabase) |
| Hosting | Render + Cloudflare Tunnel (dev) |

## Setup

```bash
python -m venv .venv
source .venv/Scripts/activate   # Windows: Scripts; Linux/Mac: bin
pip install -r requirements.txt
cp .env.example .env
```

## Running

```bash
# Dev server
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

# Expose via Cloudflare Tunnel (dev webhook)
cloudflared tunnel --url http://localhost:8000
```

## Testing & Linting

```bash
pytest tests/
ruff check src/
```

## Bot Commands

| Command | Description |
|---|---|
| `/start` | Welcome message |
| `/ajuda` | List all commands |
| `/relatorio [semana\|anterior\|mes\|MM/AAAA]` | Expense report for a period |
| `/exportar [semana\|anterior\|mes\|MM/AAAA]` | Export expenses as CSV |
| `/categorias` | List active categories |
| `/categorias add <name>` | Add a new category |

## Documentation

Full documentation lives in [`personal-finances-doc/`](../personal-finances-doc/):

- [Architecture](../personal-finances-doc/content/architecture/) — system design, hexagonal layers, request flows
- [API Reference](../personal-finances-doc/content/api-reference/) — REST endpoints, authentication, error codes
- [Security](../personal-finances-doc/content/security/) — auth model, webhook validation, access control
- [Roadmap](../personal-finances-doc/content/roadmap/) — milestones and future plans
