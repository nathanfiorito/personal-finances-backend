# CLAUDE.md — personal-finances-backend

This file provides guidance to Claude Code when working in this repository.

**Always read `specs/` before changes, and the CLAUDE.md inside the layer you are editing.**

## Project Overview

Personal Telegram bot + REST API for expense tracking. Receives payment receipts (photo, PDF, free text, or credit-card invoice PDF), extracts and categorizes expenses using AI, and exposes a REST API for the frontend. Single-user, private.

## Stack

- **Language / framework:** Java 25 / Spring Boot 3.x
- **Architecture:** Hexagonal (ports & adapters), enforced by ArchUnit
- **Build:** Maven 3.9+
- **Database:** PostgreSQL 16 + Flyway; Spring Data JPA + Hibernate `ddl-auto=validate`
- **Auth:** Spring Security + JWT (JJWT, HS256). Single admin user.
- **LLM:** Claude Sonnet (vision) + Haiku (text) via **OpenRouter**, `openai-java` SDK
- **Telegram bot:** direct `RestClient` calls, webhook mode
- **PDF parsing:** Apache PDFBox
- **Observability:** OpenTelemetry Spring Boot starter → self-hosted SigNoz
- **API docs:** SpringDoc OpenAPI (Swagger UI, disabled by default)
- **Testing:** JUnit 5 + AssertJ + Testcontainers + ArchUnit; JaCoCo coverage ≥ 80%

## Commands

```bash
cd app && mvn spring-boot:run          # dev server
cd app && mvn verify                   # all tests (needs Docker)
cd app && mvn test                     # unit tests only
cd app && mvn package -DskipTests      # build jar
cloudflared tunnel --url http://localhost:8080   # dev webhook
```

Base package: `br.com.nathanfiorito.finances`. Entry point: `app/src/main/java/br/com/nathanfiorito/finances/FinancesApplication.java`.

## Layout — read the CLAUDE.md inside each layer before editing it

- `app/src/main/java/.../domain/` — records, ports, enums, exceptions. No framework imports. See `.../domain/CLAUDE.md`.
- `app/src/main/java/.../application/` — use cases and command/query records. See `.../application/CLAUDE.md`.
- `app/src/main/java/.../infrastructure/` — Spring, JPA, JWT, OpenRouter, Telegram, observability. See `.../infrastructure/CLAUDE.md`.
- `app/src/main/java/.../interfaces/` — REST controllers, webhook, DTOs, global exception handler. See `.../interfaces/CLAUDE.md`.
- `app/src/main/resources/db/migration/` — Flyway SQL. See `.../db/migration/CLAUDE.md`.
- `app/src/test/java/.../` — unit + integration tests, stubs. See `.../test/java/br/com/nathanfiorito/finances/CLAUDE.md`.

Bounded contexts present in every layer: `transaction`, `category`, `card`, `invoice`, `telegram`, plus `shared`.

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `DB_URL` | Yes | — | JDBC URL. Example: `jdbc:postgresql://localhost:5432/finances` |
| `DB_USERNAME` | Yes | — | DB username |
| `DB_PASSWORD` | Yes | — | DB password |
| `JWT_SECRET` | Yes | — | Base64-encoded HS256 key (min 32 bytes). Generate: `openssl rand -base64 32` |
| `APP_ADMIN_EMAIL` | Yes | — | Admin login email (`POST /api/auth/login`) |
| `APP_ADMIN_PASSWORD_HASH` | Yes | — | BCrypt hash of admin password |
| `OPENROUTER_API_KEY` | Yes | — | OpenRouter API key |
| `TELEGRAM_BOT_TOKEN` | Yes | — | Telegram bot token from BotFather |
| `TELEGRAM_WEBHOOK_SECRET` | Yes | — | Expected value of `X-Telegram-Bot-Api-Secret-Token` |
| `TELEGRAM_ALLOWED_CHAT_ID` | Yes | — | Authorised chat ID |
| `CORS_ALLOWED_ORIGINS` | No | `http://localhost:3000` | Comma-separated CORS origins |
| `SIGNOZ_OTLP_ENDPOINT` | Yes | — | OTLP/HTTP endpoint for SigNoz |
| `SWAGGER_ENABLED` | No | `false` | Toggle SpringDoc Swagger UI + `/v3/api-docs` |

`jwt.expiration-seconds` (7 days) and `app.api.base-path` (`/api/v1`) are hard-coded in `application.properties`.

## Testing Standards

- Every change ships with unit **and** integration tests. Coverage ≥ **80%** via JaCoCo.
- Entity or Flyway migration changes require a Testcontainers-backed `*IT.java`. Detail: `app/src/test/java/br/com/nathanfiorito/finances/CLAUDE.md`.

## Specs

Design specs in `specs/` — read before touching the area:

- `specs/frontend-api.spec.md` — REST contract shared with the frontend.
- `specs/2026-04-14-signoz-observability-design.md` — SigNoz/OTel integration.

## Git workflow

Never commit to `main` or `develop`. Branch (`feature/*`, `fix/*`, `chore/*`), open a PR into `develop`. `develop` → `main` for releases.
