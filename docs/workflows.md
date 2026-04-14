# Backend — Workflows

## Run the dev server locally

```bash
source .venv/Scripts/activate   # or bin/activate on Linux/Mac
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

Set `ENVIRONMENT=development` in `.env` to expose `/openapi.json` at http://localhost:8000/openapi.json.

## Expose dev server to Telegram (webhook)

```bash
# In a second terminal:
cloudflared tunnel --url http://localhost:8000
# Copy the https URL it prints, e.g. https://abc123.trycloudflare.com
# Then register it as the Telegram webhook:
curl "https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://abc123.trycloudflare.com/webhook&secret_token=<TELEGRAM_WEBHOOK_SECRET>"
```

## Run all tests

```bash
pytest tests/ -v
```

## Run a specific test file

```bash
pytest tests/v2/adapters/test_expense_repository.py -v
```

## Add a new dependency

```bash
pip install <package>
pip freeze > requirements.txt
git add requirements.txt
```

## Add a new feature end-to-end

1. Create the use case in `src/v2/domain/use_cases/<domain>/`.
2. Add/update the port in `src/v2/domain/ports/` if needed.
3. Implement the adapter in `src/v2/adapters/secondary/`.
4. Wire use case + adapter in `src/v2/bootstrap.py`.
5. Add the router endpoint in `src/v2/adapters/primary/bff/routers/`.
6. Write tests in `tests/v2/`.
7. Run `pytest tests/ -v` and `ruff check src/`.
8. Commit.
