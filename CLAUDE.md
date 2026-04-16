# CLAUDE.md — personal-finances-backend

This file provides guidance to Claude Code when working in this repository.

**Always read `docs/` and `specs/` files (if any) before making changes.**

## Project Overview

Personal Telegram bot for expense tracking. Receives payment receipts (photo, PDF, or free text), extracts and categorizes expenses using AI, and exposes a REST API for the frontend. Single-user, private use.

## Stack

- **Language / framework:** Java 25 / Spring Boot 3.4.5
- **Architecture:** Hexagonal (ports & adapters), enforced by ArchUnit
- **Build:** Maven 3.9+
- **Database:** PostgreSQL 16 + Flyway migrations; Spring Data JPA + Hibernate; `ddl-auto=validate`
- **Auth:** Spring Security + JWT (JJWT 0.12.6, HS256). Single admin user. Credentials via env vars.
- **LLM:** Claude Sonnet 4.6 (vision) and Haiku 4.5 (text) via **OpenRouter** (OpenAI-compatible API). HTTP via `openai-java` 4.31.0.
- **Telegram bot:** direct `RestClient` calls to Telegram Bot API, webhook mode
- **PDF parsing:** Apache PDFBox 3.0.3 (extract text from PDF receipts before feeding to LLM)
- **Observability:** OpenTelemetry Spring Boot starter (traces + logs via OTLP/HTTP to self-hosted SigNoz); Logstash Logback encoder for structured JSON logs
- **API docs:** SpringDoc OpenAPI 2.8.5 (Swagger UI, disabled by default via `SWAGGER_ENABLED`)
- **Testing:** JUnit 5 + AssertJ + Spring Security Test + Testcontainers (PostgreSQL) + ArchUnit + OTel SDK testing utilities; JaCoCo for coverage
- **Hosting:** Hostinger VPS with Coolify (prod) + Cloudflare Tunnel (dev webhook)

## Commands

```bash
# Run dev server (from this repo root)
cd app && mvn spring-boot:run

# Run all tests (unit + integration + architecture) — Docker required for Testcontainers
cd app && mvn verify

# Run unit tests only (no Docker)
cd app && mvn test

# Build jar
cd app && mvn package -DskipTests

# Expose local server via Cloudflare Tunnel (dev webhook)
cloudflared tunnel --url http://localhost:8080

# JaCoCo coverage report → app/target/site/jacoco/index.html
```

## Architecture

Hexagonal (ports & adapters). Entry point: `app/src/main/java/br/com/nathanfiorito/finances/FinancesApplication.java`.

Base package: `br.com.nathanfiorito.finances`

### Package layout

```
app/src/main/java/br/com/nathanfiorito/finances/
├── FinancesApplication.java            — Spring Boot entry point
│
├── domain/                              — Pure business logic (no framework imports)
│   ├── transaction/
│   │   ├── records/                     — Transaction, TransactionUpdate, ExtractedTransaction,
│   │   │                                   SummaryItem, MonthlyItem, MonthlyCategoryItem
│   │   ├── enums/                       — TransactionType (EXPENSE/INCOME), PaymentMethod (CREDIT/DEBIT)
│   │   ├── ports/                       — TransactionRepository, LlmPort
│   │   └── exceptions/                  — TransactionNotFoundException, LlmExtractionException
│   ├── category/
│   │   ├── records/                     — Category
│   │   ├── ports/                       — CategoryRepository
│   │   └── exceptions/                  — CategoryNotFoundException
│   ├── telegram/
│   │   ├── records/                     — PendingTransaction
│   │   └── ports/                       — NotifierPort, PendingStatePort
│   └── shared/
│       └── PageResult.java              — Generic paginated result
│
├── application/                         — Use cases (orchestrate domain, call ports)
│   ├── transaction/
│   │   ├── commands/                    — CreateTransactionCommand, UpdateTransactionCommand,
│   │   │                                   DeleteTransactionCommand
│   │   ├── queries/                     — ListTransactionsQuery, GetTransactionQuery,
│   │   │                                   GetSummaryQuery, GetMonthlyQuery, ExportCsvQuery
│   │   └── usecases/                    — Create/Update/Delete/Get/List/GetSummary/GetMonthly/
│   │                                       ExportCsv TransactionUseCase
│   ├── category/
│   │   ├── commands/                    — Create / Update / Deactivate CategoryCommand
│   │   ├── queries/                     — ListCategoriesQuery
│   │   └── usecases/                    — Create / Update / Deactivate / ListCategories UseCase
│   └── telegram/
│       ├── commands/                    — ProcessMessageCommand, ConfirmTransactionCommand,
│       │                                   CancelTransactionCommand, ChangeCategoryCommand
│       ├── usecases/                    — ProcessMessage / Confirm / Cancel / ChangeCategory UseCase
│       └── AmountFormatter.java         — pt-BR currency formatting helper
│
├── infrastructure/                      — Adapters (Spring, JPA, HTTP clients, observability)
│   ├── config/
│   │   ├── UseCaseConfig.java           — Spring @Configuration wiring use cases as beans
│   │   └── OpenApiConfig.java           — SpringDoc OpenAPI / Swagger UI setup
│   ├── security/
│   │   ├── SecurityConfig.java          — Spring Security filter chain, CORS, JWT filter order
│   │   ├── JwtAuthFilter.java           — validates Authorization: Bearer <jwt>
│   │   ├── JwtService.java              — generate / parse HS256 JWTs
│   │   └── TelegramWebhookFilter.java   — validates X-Telegram-Bot-Api-Secret-Token (runs before JwtAuthFilter)
│   ├── transaction/
│   │   ├── adapter/                     — TransactionRepositoryAdapter (implements TransactionRepository)
│   │   ├── entity/                      — TransactionEntity (@Entity)
│   │   ├── mapper/                      — TransactionMapper (static)
│   │   └── repository/                  — JpaTransactionRepository (Spring Data JPA)
│   ├── category/
│   │   ├── adapter/                     — CategoryRepositoryAdapter
│   │   ├── entity/                      — CategoryEntity
│   │   ├── mapper/                      — CategoryMapper
│   │   └── repository/                  — JpaCategoryRepository
│   ├── llm/
│   │   ├── config/                      — OpenRouterConfig (OpenAI SDK client bean pointed at OpenRouter)
│   │   └── adapter/                     — OpenRouterLlmAdapter (implements LlmPort), LlmCallResult,
│   │                                       LlmExtractionResponse, LlmCategorizeResponse, LlmDuplicateResponse
│   └── telegram/
│       ├── config/                      — TelegramConfig, TelegramProperties (@ConfigurationProperties)
│       ├── notifier/                    — TelegramNotifierAdapter (implements NotifierPort)
│       ├── file/                        — TelegramFileDownloaderAdapter, DownloadedFile
│       └── pending/                     — InMemoryPendingStateAdapter (ConcurrentHashMap + TTL 10 min)
│
└── interfaces/                          — Inbound adapters (HTTP, webhook)
    ├── rest/
    │   ├── auth/                        — AuthController (POST /api/auth/login), LoginRequest/Response DTOs
    │   ├── transaction/                 — TransactionController + request/response DTOs
    │   ├── category/                    — CategoryController + DTOs
    │   ├── report/                      — ReportController (/reports/summary, /reports/monthly, /export/csv)
    │   ├── bff/                         — BffController (/bff/transactions — shape for frontend)
    │   └── shared/                      — GlobalExceptionHandler, PageResponse
    └── telegram/
        ├── TelegramWebhookController.java  — POST /webhook entry point
        └── dto/                            — TelegramUpdateDto and friends
```

### Request flow (Telegram bot)

1. `POST /webhook` → `TelegramWebhookFilter` validates `X-Telegram-Bot-Api-Secret-Token` and chat ID
2. `TelegramWebhookController` routes to message / command / callback handler
3. `ProcessMessageUseCase`:
   - If image: Sonnet 4.6 vision → `ExtractedTransaction`
   - If PDF: PDFBox extracts text → Haiku 4.5 → `ExtractedTransaction`
   - If text: Haiku 4.5 directly
4. Bot sends inline-keyboard confirmation via `NotifierPort`
5. Pending state persisted in `InMemoryPendingStateAdapter` (ConcurrentHashMap, 10-min TTL)
6. On user confirm (callback): `ConfirmTransactionUseCase` → `LlmPort.isDuplicate()` (Haiku) → `TransactionRepository.save()`
7. Cancel / change category go through their own use cases on the same pending entry

### REST API

- Base path: `app.api.base-path=/api/v1` (configurable in `application.properties`)
- All routes are JWT-protected **except**:
  - `/api/auth/**` (login)
  - `/webhook` (Telegram, protected by its own secret-token filter)
  - `/swagger-ui/**`, `/swagger-ui.html`, `/v3/api-docs/**` (permit-all; when `SWAGGER_ENABLED=false` SpringDoc registers no handlers and returns 404)

| Method | Path | Controller |
|---|---|---|
| POST | `/api/auth/login` | AuthController |
| GET \| POST | `/api/v1/transactions` | TransactionController |
| GET \| PUT \| DELETE | `/api/v1/transactions/{id}` | TransactionController |
| GET | `/api/v1/bff/transactions` | BffController (shape optimized for frontend) |
| GET \| POST | `/api/v1/categories` | CategoryController |
| PATCH \| DELETE | `/api/v1/categories/{id}` | CategoryController |
| GET | `/api/v1/reports/summary?start=&end=` | ReportController |
| GET | `/api/v1/reports/monthly?year=` | ReportController |
| GET | `/api/v1/export/csv?start=&end=` | ReportController (UTF-8 BOM) |
| POST | `/webhook` | TelegramWebhookController |

Errors funnel through `interfaces/rest/shared/GlobalExceptionHandler`.

### Database

Managed by Flyway. Migrations in `app/src/main/resources/db/migration/`:

| Version | File | Summary |
|---|---|---|
| V1 | `V1__init.sql` | Creates `categories` and `transactions` tables + indexes on transactions (date, category_id, (date, category_id), transaction_type) |
| V2 | `V2__confidence_to_double.sql` | `transactions.confidence` → `DOUBLE PRECISION` |

**Schema at a glance:**

- `categories(id SERIAL PK, name UNIQUE, active BOOL, created_at, updated_at)`
- `transactions(id UUID PK, amount DECIMAL(10,2), date, establishment, description, category_id FK, tax_id, entry_type CHECK ∈ {image,text,pdf,manual}, transaction_type CHECK ∈ {EXPENSE,INCOME}, payment_method CHECK ∈ {CREDIT,DEBIT}, confidence DOUBLE PRECISION, created_at, updated_at)`

Hibernate runs in `validate` mode — any schema drift from entities fails startup, forcing migrations for every change.

### Jackson / JSON conventions

Set in `application.properties`:

- `SNAKE_CASE` property naming (API uses snake_case, Java uses camelCase)
- Non-null default inclusion (omit null fields from responses)
- Dates serialized as ISO-8601 strings (not timestamps)
- Case-insensitive enum deserialization
- Unknown properties ignored on input

### Observability (SigNoz / OpenTelemetry)

Traces and logs ship to a self-hosted SigNoz via OTLP. Design spec: `specs/2026-04-14-signoz-observability-design.md`.

- `opentelemetry-spring-boot-starter` auto-instruments Spring MVC, JDBC, and the Logback log bridge — no Java agent required.
- Manual span added in `OpenRouterLlmAdapter` for LLM calls (tracer injected).
- Structured JSON logs via `logstash-logback-encoder` (stdout, also exported over OTLP).
- Metrics exporter is **disabled** (`otel.metrics.exporter=none`); traces + logs only.
- Service name: `finances-backend`. Propagators: `tracecontext,baggage`. Protocol: `http/protobuf`.
- `OTel SDK testing` (`InMemorySpanExporter`) is available in tests for span assertions.

### Key design decisions

- **OpenRouter, not Anthropic direct.** Base URL `https://openrouter.ai/api/v1`; model IDs `anthropic/claude-sonnet-4-6` and `anthropic/claude-haiku-4-5`. Client built on `openai-java` (OpenRouter is OpenAI-compatible).
- **Two models by concern.** Sonnet 4.6 for image vision; Haiku 4.5 for text extraction, categorization, and duplicate checking.
- **Mandatory confirmation.** Never persist without explicit user confirmation. Pending state is in-memory only (`InMemoryPendingStateAdapter`) with a 10-min TTL — restarts lose pending confirmations by design.
- **Webhook security ordering.** `TelegramWebhookFilter` runs *before* `JwtAuthFilter` in the Spring Security chain, so `/webhook` never reaches the JWT filter.
- **Architecture enforced by ArchUnit.** `HexagonalArchitectureTest` asserts: domain must not depend on application or infrastructure; application must not depend on infrastructure or `interfaces`; Spring annotations forbidden in domain.
- **Swagger gated but always permitted.** When `SWAGGER_ENABLED=false`, SpringDoc registers no handlers (→ 404); when `true`, the spec is publicly accessible without auth. Acceptable for a private single-user app.

### Bot commands

| Command | Description |
|---|---|
| `/start` | Welcome message |
| `/ajuda` | List all commands |
| `/relatorio [semana\|anterior\|mes\|MM/AAAA]` | Expense report for a period |
| `/exportar [semana\|anterior\|mes\|MM/AAAA]` | Export expenses as CSV |
| `/categorias` | List active categories |
| `/categorias add <name>` | Add a new category |

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `DB_URL` | Yes | — | JDBC URL. Example: `jdbc:postgresql://localhost:5432/finances` |
| `DB_USERNAME` | Yes | — | Database username |
| `DB_PASSWORD` | Yes | — | Database password |
| `JWT_SECRET` | Yes | — | Base64-encoded HS256 key (min 32 bytes). Generate: `openssl rand -base64 32` |
| `APP_ADMIN_EMAIL` | Yes | — | Admin login email (`POST /api/auth/login`) |
| `APP_ADMIN_PASSWORD_HASH` | Yes | — | BCrypt hash of admin password |
| `OPENROUTER_API_KEY` | Yes | — | OpenRouter API key |
| `TELEGRAM_BOT_TOKEN` | Yes | — | Telegram bot token from BotFather |
| `TELEGRAM_WEBHOOK_SECRET` | Yes | — | Value expected in `X-Telegram-Bot-Api-Secret-Token` header |
| `TELEGRAM_ALLOWED_CHAT_ID` | Yes | — | Telegram chat ID authorised to use the bot |
| `CORS_ALLOWED_ORIGINS` | No | `http://localhost:3000` | Comma-separated CORS origins |
| `SIGNOZ_OTLP_ENDPOINT` | Yes | — | OTLP/HTTP endpoint for SigNoz (traces + logs). Example: `http://signoz.internal:4318` |
| `SWAGGER_ENABLED` | No | `false` | Toggle SpringDoc Swagger UI + `/v3/api-docs` |

`jwt.expiration-seconds` is hard-coded at 604800 (7 days) in `application.properties`. `app.api.base-path` is hard-coded at `/api/v1`.

## Tests

Layout under `app/src/test/java/br/com/nathanfiorito/finances/`:

- `application/**/usecases/*Test.java` — use-case unit tests (plain JUnit + AssertJ + `stubs/`)
- `domain/**/Test.java` — domain record / enum tests
- `infrastructure/**/Test.java` — pure unit tests (mappers, entities)
- `infrastructure/**/*IT.java` + `BaseRepositoryIT.java` — Testcontainers-backed JPA integration tests
- `interfaces/rest/**/*IT.java` + `BaseControllerIT.java` — full Spring Boot `@SpringBootTest` integration tests (MockMvc, real PostgreSQL via Testcontainers)
- `interfaces/rest/swagger/SwaggerSecurityIT.java` — verifies Swagger permit-all + toggle behavior
- `architecture/HexagonalArchitectureTest.java` — ArchUnit rules
- `stubs/` — hand-written test doubles (`StubCategoryRepository`, `StubLlmPort`, `StubNotifierPort`, `StubPendingStatePort`, `StubTransactionRepository`) — prefer these over Mockito for use-case tests

**Run a single test:**
```bash
cd app && mvn test -Dtest=CreateTransactionUseCaseTest
cd app && mvn verify -Dit.test=TransactionControllerIT   # integration tests
```

## Specs

Design specs live in `specs/` and should be read before touching the related area:

- `specs/frontend-api.spec.md` — REST contract shared with the frontend
- `specs/2026-04-14-signoz-observability-design.md` — SigNoz/OTel integration design

## Git workflow

**Never commit directly to `main` or `develop`.** Always branch (`feature/*`, `fix/*`, `chore/*`) and open a PR into `develop`. `develop` → `main` for releases.
