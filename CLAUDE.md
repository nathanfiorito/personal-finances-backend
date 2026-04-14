# CLAUDE.md — personal-finances-backend

This file provides guidance to Claude Code when working in this repository.

**Always read `docs/` files (if any) before making changes.**

## Project Overview

Personal Telegram bot for expense tracking. Receives payment receipts (photo, PDF, or free text), extracts and categorizes expenses using AI, and exposes a REST API for the frontend. Single-user, private use.

## Stack

- **Backend:** Java 25 / Spring Boot 3.x, hexagonal (ports & adapters) architecture
- **Build:** Maven 3.9+
- **Bot:** RestClient (direct HTTP calls to Telegram Bot API, webhook mode)
- **LLM:** Claude Sonnet 4.6 (vision) and Haiku 4.5 (text extraction, categorization, duplicate check) via **OpenRouter** (OpenAI-compatible API)
- **Database:** PostgreSQL with Flyway migrations; Spring Data JPA + Hibernate
- **Auth:** JWT (HS256 via JJWT 0.12.x); credentials stored as env vars
- **Hosting:** Hostinger VPS with Coolify (prod) + Cloudflare Tunnel (dev)
- **Testing:** JUnit 5 + AssertJ + Testcontainers (integration) + ArchUnit (architecture)

## Commands

```bash
# Run dev server (from repo root)
cd app && mvn spring-boot:run

# Run all tests (unit + integration + architecture) — Docker required
cd app && mvn verify

# Run unit tests only (no Docker)
cd app && mvn test

# Build jar
cd app && mvn package -DskipTests

# Expose local server via Cloudflare Tunnel (dev webhook)
cloudflared tunnel --url http://localhost:8080
```

## Architecture

Hexagonal (ports & adapters). Entry point: `app/src/main/java/br/com/nathanfiorito/finances/FinancesApplication.java`.

Base package: `br.com.nathanfiorito.finances`

### Package layout

```
app/src/main/java/br/com/nathanfiorito/finances/
├── FinancesApplication.java         — Spring Boot entry point
├── domain/                          — Pure business logic (no framework imports)
│   ├── transaction/
│   │   ├── records/                 — Transaction, ExtractedTransaction, SummaryItem, etc.
│   │   ├── ports/                   — TransactionRepository (interface), LlmPort (interface)
│   │   ├── enums/                   — TransactionType, PaymentMethod
│   │   └── exceptions/              — TransactionNotFoundException, LlmExtractionException
│   ├── category/
│   │   ├── records/                 — Category
│   │   ├── ports/                   — CategoryRepository (interface)
│   │   └── exceptions/              — CategoryNotFoundException
│   ├── telegram/
│   │   ├── records/                 — PendingTransaction
│   │   └── ports/                   — NotifierPort, PendingStatePort
│   └── shared/
│       └── PageResult.java          — Generic paginated result
├── application/                     — Use cases (orchestrate domain, call ports)
│   ├── transaction/
│   │   ├── commands/                — CreateTransactionCommand, UpdateTransactionCommand, etc.
│   │   ├── queries/                 — ListTransactionsQuery, GetTransactionQuery, etc.
│   │   └── usecases/                — CreateTransactionUseCase, ListTransactionsUseCase, etc.
│   ├── category/
│   │   ├── commands/                — CreateCategoryCommand, UpdateCategoryCommand, etc.
│   │   ├── queries/                 — ListCategoriesQuery
│   │   └── usecases/                — CreateCategoryUseCase, UpdateCategoryUseCase, etc.
│   └── telegram/
│       ├── commands/                — ProcessMessageCommand, ConfirmTransactionCommand, etc.
│       └── usecases/                — ProcessMessageUseCase, ConfirmTransactionUseCase, etc.
└── infrastructure/                  — Adapters (Spring, JPA, HTTP clients)
    ├── config/
    │   └── UseCaseConfig.java       — Spring @Configuration wiring use cases as beans
    ├── transaction/
    │   ├── adapter/                 — TransactionRepositoryAdapter (implements TransactionRepository)
    │   ├── entity/                  — TransactionEntity (@Entity)
    │   ├── mapper/                  — TransactionMapper (static)
    │   └── repository/              — JpaTransactionRepository (Spring Data JPA)
    ├── category/
    │   ├── adapter/                 — CategoryRepositoryAdapter
    │   ├── entity/                  — CategoryEntity
    │   ├── mapper/                  — CategoryMapper
    │   └── repository/              — JpaCategoryRepository
    ├── llm/
    │   └── adapter/                 — OpenRouterLlmAdapter (implements LlmPort)
    ├── telegram/
    │   ├── adapter/                 — TelegramNotifierAdapter, InMemoryPendingStateAdapter
    │   ├── controller/              — TelegramWebhookController (POST /webhook)
    │   └── filter/                  — TelegramWebhookFilter (validates secret token)
    └── web/
        ├── auth/                    — AuthController (POST /api/auth/login), JwtAuthFilter
        ├── bff/                     — TransactionController, CategoryController, ReportController
        └── security/                — Spring Security config
```

### Request flow (Telegram bot)

1. `POST /webhook` → `TelegramWebhookFilter` validates `X-Telegram-Bot-Api-Secret-Token`
2. `TelegramWebhookController` routes to message, command, or callback handler
3. `ProcessMessageUseCase`: calls `LlmPort.extract()` → `ExtractedTransaction`
4. Bot sends confirmation via Telegram inline keyboard (`NotifierPort`)
5. On confirmation: `ConfirmTransactionUseCase` → `LlmPort.isDuplicate()` → `TransactionRepository.save()`

### REST API

Routes at `/api/v1/...`, all protected by JWT except `/api/auth/login` and `/webhook`.

### Key design decisions

- **OpenRouter, not Anthropic direct:** base URL `https://openrouter.ai/api/v1`, model IDs `anthropic/claude-sonnet-4-6` and `anthropic/claude-haiku-4-5`.
- **Two models:** Sonnet 4.6 for image vision; Haiku 4.5 for text extraction, categorization, duplicate checking.
- **Mandatory confirmation:** Never persist without explicit user confirmation. Pending state in `InMemoryPendingStateAdapter` (ConcurrentHashMap + TTL 10 min).
- **Webhook security:** `TelegramWebhookFilter` validates secret token header before the JWT filter.
- **Architecture enforced by ArchUnit:** domain must not depend on application or infrastructure; application must not depend on infrastructure.

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

| Variable | Required | Description |
|---|---|---|
| `DB_URL` | Yes | JDBC URL. Example: `jdbc:postgresql://localhost:5432/finances` |
| `DB_USERNAME` | Yes | Database username |
| `DB_PASSWORD` | Yes | Database password |
| `JWT_SECRET` | Yes | Base64-encoded HS256 key (min 32 bytes). Generate: `openssl rand -base64 32` |
| `APP_ADMIN_EMAIL` | Yes | Admin login email |
| `APP_ADMIN_PASSWORD_HASH` | Yes | BCrypt hash of admin password |
| `OPENROUTER_API_KEY` | Yes | OpenRouter API key |
| `TELEGRAM_BOT_TOKEN` | Yes | Telegram bot token from BotFather |
| `TELEGRAM_WEBHOOK_SECRET` | Yes | Secret for `X-Telegram-Bot-Api-Secret-Token` header |
| `TELEGRAM_ALLOWED_CHAT_ID` | Yes | Telegram chat ID authorised to use the bot |
| `CORS_ALLOWED_ORIGINS` | No | Comma-separated CORS origins (default: `http://localhost:3000`) |
