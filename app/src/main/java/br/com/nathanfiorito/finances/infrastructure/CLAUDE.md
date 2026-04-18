# CLAUDE.md — infrastructure/

## Purpose

Outbound adapters. Spring, JPA, HTTP clients, security, observability wiring. Everything that depends on a framework or external service and implements a port from `domain/`.

## Package Layout

```
infrastructure/
├── config/
│   ├── UseCaseConfig.java    wires every use case as a Spring @Bean
│   └── OpenApiConfig.java    SpringDoc / Swagger UI setup (gated by SWAGGER_ENABLED)
├── security/
│   ├── SecurityConfig.java         filter chain, CORS, JWT filter order
│   ├── JwtAuthFilter.java          validates Authorization: Bearer <jwt>
│   ├── JwtService.java             generate / parse HS256 JWTs (JJWT)
│   └── TelegramWebhookFilter.java  validates X-Telegram-Bot-Api-Secret-Token (runs before JwtAuthFilter)
├── transaction/      adapter, entity, mapper, repository (JPA)
├── category/         adapter, entity, mapper, repository (JPA)
├── card/             adapter, entity, mapper, repository (JPA)
├── invoice/          adapter only (prediction persistence lives under card/)
├── llm/
│   ├── config/       OpenRouterConfig — OpenAI SDK client bean pointed at OpenRouter
│   └── adapter/      OpenRouterLlmAdapter (implements LlmPort), LlmCallResult,
│                     LlmExtractionResponse, LlmCategorizeResponse, LlmDuplicateResponse
└── telegram/
    ├── config/       TelegramConfig, TelegramProperties (@ConfigurationProperties)
    ├── notifier/     TelegramNotifierAdapter (implements NotifierPort)
    ├── file/         TelegramFileDownloaderAdapter, DownloadedFile
    └── pending/      InMemoryPendingStateAdapter (ConcurrentHashMap + TTL 10 min)
```

## Per-context adapter pattern

Each JPA-backed context has four siblings:

- `adapter/` — implements the domain port (`TransactionRepositoryAdapter implements TransactionRepository`).
- `entity/` — `@Entity` class with `jakarta.persistence` annotations.
- `mapper/` — static `toEntity(record)` / `toDomain(entity)` pair.
- `repository/` — Spring Data JPA interface (`JpaTransactionRepository extends JpaRepository<...>`).

Domain records never cross into entities. The adapter is the only class that knows about both.

## Security

- Spring Security + JJWT (HS256). Single admin user; no registration endpoint.
- Credentials from `APP_ADMIN_EMAIL` (plain) and `APP_ADMIN_PASSWORD_HASH` (BCrypt).
- `POST /api/auth/login` returns a JWT valid for 7 days (`jwt.expiration-seconds=604800`, hard-coded).
- All `/api/v1/**` routes require `Authorization: Bearer <jwt>`.
- `/webhook` is protected by `TelegramWebhookFilter` — which runs **before** `JwtAuthFilter` so the webhook never reaches the JWT filter.
- `/swagger-ui/**` and `/v3/api-docs/**` are permit-all; SpringDoc only registers handlers when `SWAGGER_ENABLED=true`.

## LLM

- **OpenRouter, not Anthropic direct.** Base URL `https://openrouter.ai/api/v1`.
- Model IDs: `anthropic/claude-sonnet-4-6` (vision) and `anthropic/claude-haiku-4-5` (text).
- HTTP via `openai-java` SDK (OpenRouter is OpenAI-compatible).
- Manual OTel span added in `OpenRouterLlmAdapter` for each LLM call.

## Observability (SigNoz / OpenTelemetry)

- `opentelemetry-spring-boot-starter` auto-instruments Spring MVC, JDBC, and the Logback log bridge — no Java agent required.
- Structured JSON logs via `logstash-logback-encoder` (stdout, also exported over OTLP).
- Metrics exporter is **disabled** (`otel.metrics.exporter=none`); traces + logs only.
- Service name: `finances-backend`. Propagators: `tracecontext,baggage`. Protocol: `http/protobuf`.
- Endpoint via `SIGNOZ_OTLP_ENDPOINT`.
- `InMemorySpanExporter` available in tests for span assertions.
- Design spec: `specs/2026-04-14-signoz-observability-design.md`.

## Pending state (Telegram)

`InMemoryPendingStateAdapter` is a `ConcurrentHashMap` keyed by chat ID with a 10-minute TTL. Process restart drops every pending confirmation — acceptable for a single-user app.

## When to update this file

- New adapter → add the context to Package Layout.
- New env var or hard-coded security constant → update here and in the backend root CLAUDE.md env var table.

## Pointers

- Ports this layer implements: `../domain/CLAUDE.md`.
- Who calls these adapters indirectly (through ports): `../application/CLAUDE.md`.
- Migrations that must match each `@Entity`: `../../../resources/db/migration/CLAUDE.md`.
