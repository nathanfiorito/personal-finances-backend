# SigNoz Observability Integration — Design Spec

**Date:** 2026-04-14
**Status:** Approved
**Scope:** `personal-finances-backend`

## Goal

Integrate distributed tracing and structured logging into the Spring Boot backend, shipping signals to a self-hosted SigNoz instance via OpenTelemetry (OTLP).

**Out of scope (for now):** metrics export to SigNoz.

---

## Signals

| Signal | Destination | Priority |
|---|---|---|
| Traces | SigNoz (OTLP/gRPC) | 1 |
| Logs | stdout (JSON) + SigNoz (OTLP) | 1 |
| Metrics | disabled | deferred |

---

## Approach

**OTel Spring Boot Starter (code-based SDK, no Java agent).**

`io.opentelemetry.instrumentation:opentelemetry-spring-boot-starter` (via `opentelemetry-instrumentation-bom`) provides auto-instrumentation for Spring MVC and JDBC, plus a Logback log bridge — all managed in `pom.xml`, version-controlled, no JAR to manage on the VPS.

---

## Dependencies

Add to `pom.xml`:

```xml
<!-- In <dependencyManagement> -->
<dependency>
    <groupId>io.opentelemetry.instrumentation</groupId>
    <artifactId>opentelemetry-instrumentation-bom</artifactId>
    <version>2.15.0</version>
    <type>pom</type>
    <scope>import</scope>
</dependency>

<!-- In <dependencies> -->
<dependency>
    <groupId>io.opentelemetry.instrumentation</groupId>
    <artifactId>opentelemetry-spring-boot-starter</artifactId>
</dependency>
<dependency>
    <groupId>net.logstash.logback</groupId>
    <artifactId>logstash-logback-encoder</artifactId>
    <version>8.1</version>
</dependency>
```

The OTLP exporter is pulled in transitively by the starter.

---

## Configuration (`application.properties`)

```properties
# OpenTelemetry
otel.service.name=finances-backend
otel.exporter.otlp.endpoint=${SIGNOZ_OTLP_ENDPOINT}
otel.exporter.otlp.protocol=grpc
otel.logs.exporter=otlp
otel.traces.exporter=otlp
otel.metrics.exporter=none
otel.propagators=tracecontext,baggage
```

**New environment variable:**

| Variable | Required | Description |
|---|---|---|
| `SIGNOZ_OTLP_ENDPOINT` | Yes | SigNoz OTLP endpoint. Example: `https://signoz-otel.nathanfiorito.com.br` |

---

## Tracing

### Auto-instrumented (zero code changes)

| Source | Spans produced |
|---|---|
| Spring MVC (`/webhook`, `/api/v1/**`, `/api/auth/login`) | One span per request: method, URL, HTTP status, duration |
| `TelegramWebhookFilter`, `JwtAuthFilter` | Filter execution within the request span |
| JDBC / Hibernate | One span per SQL query: statement, table, duration |
| Flyway (startup) | Migration spans |

### Manual spans — `OpenRouterLlmAdapter`

The `Tracer` bean is injected into `OpenRouterLlmAdapter`. Each OpenRouter call is wrapped in a child span:

**Span name:** `llm.openrouter/<operation>`
(e.g. `llm.openrouter/extract`, `llm.openrouter/isDuplicate`, `llm.openrouter/categorize`)

**Span attributes:**

| Attribute | Value |
|---|---|
| `llm.model` | `"anthropic/claude-sonnet-4-6"` or `"anthropic/claude-haiku-4-5"` |
| `llm.operation` | `"extract"` \| `"isDuplicate"` \| `"categorize"` |
| `llm.input.tokens` | token count from OpenRouter response |
| `llm.output.tokens` | token count from OpenRouter response |
| `llm.finish_reason` | `"stop"` \| `"length"` \| etc. |
| `error` | `true` + exception message on failure |

**Full trace example (receipt flow):**

```
POST /webhook
  └── TelegramWebhookFilter
  └── ProcessMessageUseCase
        └── SELECT * FROM categories   (JDBC span)
        └── llm.openrouter/extract     (manual span)
  └── TelegramNotifierAdapter (Telegram API call)

POST /webhook  (confirm callback)
  └── ConfirmTransactionUseCase
        └── llm.openrouter/isDuplicate  (manual span)
        └── INSERT INTO transactions    (JDBC span)
```

---

## Logging

### `logback-spring.xml`

Two appenders active in all profiles:

```
ConsoleAppender
  └── LogstashEncoder  →  structured JSON to stdout
        Fields: timestamp, level, logger, message, traceId, spanId, thread, MDC keys

OpenTelemetryAppender
  └── Forwards every log event to SigNoz Log Explorer via OTLP
        Includes traceId → links each log to its parent trace
```

### Log levels

```
br.com.nathanfiorito.finances  →  INFO   (application code)
org.springframework            →  WARN   (suppress framework noise)
org.hibernate.SQL              →  WARN   (SQL visible in traces; no stdout duplication)
```

### Log-trace correlation in SigNoz

- Open any trace in SigNoz → click a span → "View Logs" shows all logs emitted during that span
- Log Explorer: filter by `service.name=finances-backend`, `level=ERROR`, or any attribute
- stdout (for VPS log aggregation) and SigNoz Log Explorer receive the same events

---

## What is NOT changed

- Domain layer — no observability imports (hexagonal boundary preserved)
- Application use cases — no observability imports
- ArchUnit rules — no changes needed (infrastructure layer owns the `Tracer` injection)

---

## Environment Variables Summary (additions)

| Variable | Required | Example |
|---|---|---|
| `SIGNOZ_OTLP_ENDPOINT` | Yes | `https://signoz-otel.nathanfiorito.com.br` |
