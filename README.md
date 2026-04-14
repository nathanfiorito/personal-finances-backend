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

## Java Rewrite (`app/`)

A Java rewrite of this backend is in progress inside `app/`. It follows the same hexagonal (ports & adapters) architecture with a DDD-inspired package structure.

**Stack:** Java 25 · Spring Boot 3.x · Maven · Lombok · Spring Data JPA + Hibernate · JUnit 5 + AssertJ · ArchUnit · JaCoCo

### Completed

- [x] Domain layer — `Transaction`, `Category`, enums, output port interfaces, domain exceptions
- [x] Application layer — use cases (CRUD for transactions and categories), commands, queries, `PageResult<T>`
- [x] Unit tests — 74 tests with in-memory stubs, no Spring context
- [x] Architecture tests — 4 ArchUnit rules enforcing hexagonal boundaries
- [x] Infrastructure layer — Flyway migrations (`V1__init.sql`), JPA `@Entity` classes with `@Column` constraints, static mappers, `TransactionRepositoryAdapter` and `CategoryRepositoryAdapter` backed by PostgreSQL
- [x] LLM adapter — `OpenRouterLlmAdapter` implementing `LlmPort`: extracts transactions from text, PDF, and image (vision) via OpenRouter; `isDuplicate` duplicate check; Haiku 4.5 for text/pdf/duplicates, Sonnet 4.6 for images
- [x] **REST controllers** — `TransactionController`, `CategoryController`, `BffController` (`/api/v2/...`) with Spring Security + JWT auth
- [x] **JWT security filter** — HS256 JWT (JJWT 0.12.x); `POST /api/auth/login` issues tokens; `JwtAuthFilter` validates `Authorization: Bearer` on all `/api/v2/*` routes; credentials stored as env vars (`APP_ADMIN_EMAIL`, `APP_ADMIN_PASSWORD_HASH`)
- [x] **Use case wiring** — `UseCaseConfig` registers all use cases as Spring beans; ArchUnit rule `infrastructureMustNotDependOnApplication` removed to allow this wiring

### Pending

- [ ] **Telegram use cases** — `ProcessMessage`, `ConfirmTransaction`, and related handlers
- [ ] **Report use cases** — `GetMonthlySummary`, `ExportCsv`
- [ ] **Integration tests** — Testcontainers with a real PostgreSQL instance

---

## Documentation

Full documentation lives in [`personal-finances-doc/`](../personal-finances-doc/):

- [Architecture](../personal-finances-doc/content/architecture/) — system design, hexagonal layers, request flows
- [API Reference](../personal-finances-doc/content/api-reference/) — REST endpoints, authentication, error codes
- [Security](../personal-finances-doc/content/security/) — auth model, webhook validation, access control
- [Roadmap](../personal-finances-doc/content/roadmap/) — milestones and future plans
