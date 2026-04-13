# Backend — Rules

## Architecture constraints

**Do not import adapters from domain.**
The domain (`src/v2/domain/`) must never import from `src/v2/adapters/`. This is enforced by import-linter in `tests/v2/test_architecture.py`. If you need to call a service from a use case, define a port (ABC) in `src/v2/domain/ports/` and inject the implementation at startup via `bootstrap.py`.

**Do not import secondary adapters from primary adapters.**
`src/v2/adapters/primary/` (BFF, Telegram handlers) must not import directly from `src/v2/adapters/secondary/` (Supabase, OpenRouter). They receive dependencies through the use case container injected by `bootstrap.py`.

**Do not persist an expense without user confirmation.**
The `ConfirmExpense` use case is the only path to `ExpenseRepository.save()` for bot-originated data. Never call `.save()` directly from a message handler.

## LLM / API

**Use OpenRouter, not Anthropic direct.**
Model IDs are `anthropic/claude-sonnet-4-6` and `anthropic/claude-haiku-4-5` (not the Anthropic SDK format). The base URL is `https://openrouter.ai/api/v1`. The client lives in `src/v2/adapters/secondary/openrouter/llm_adapter.py`.

**Use Haiku 4.5 for cheap tasks, Sonnet 4.6 for vision/reports.**
Text extraction, categorization, and duplicate checks use Haiku. Image/PDF vision and monthly report generation use Sonnet.

## Security

**Never expose OpenAPI in production.**
`openapi_url` is set to `None` when `ENVIRONMENT=production`. Do not change this. Set `ENVIRONMENT=development` only in local `.env`.

**Always validate the Telegram secret token.**
The `X-Telegram-Bot-Api-Secret-Token` header is validated on every `/webhook` request. Do not bypass this check.
