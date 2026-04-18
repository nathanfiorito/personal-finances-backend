# CLAUDE.md — interfaces/

## Purpose

Inbound adapters. REST controllers, Telegram webhook controller, and request/response DTOs. The only layer allowed to know about HTTP and Jackson.

## Package Layout

```
interfaces/
├── rest/
│   ├── auth/         AuthController (POST /api/auth/login), LoginRequest/Response DTOs
│   ├── transaction/  TransactionController + Create/Update request + Response DTO
│   ├── category/     CategoryController + Create/Update request + Response DTO
│   ├── card/         CardController + Create/Update request + Response DTO
│   ├── invoice/      InvoiceController + InvoiceImportController + invoice/prediction/timeline/import DTOs
│   ├── report/       ReportController (summary, monthly, csv export) + DTOs
│   ├── bff/          BffController (/bff/transactions — shape optimized for frontend)
│   └── shared/       GlobalExceptionHandler, ErrorResponse, PageResponse
└── telegram/
    ├── TelegramWebhookController.java   POST /webhook entry point
    └── dto/                              TelegramUpdateDto and friends
```

## REST API

Base path: `app.api.base-path=/api/v1` (configurable). All routes JWT-protected **except** `/api/auth/**`, `/webhook`, `/swagger-ui/**`, `/v3/api-docs/**`.

| Method | Path | Controller |
|---|---|---|
| POST | `/api/auth/login` | AuthController |
| GET \| POST | `/api/v1/transactions` | TransactionController |
| GET \| PUT \| DELETE | `/api/v1/transactions/{id}` | TransactionController |
| GET | `/api/v1/bff/transactions` | BffController |
| GET \| POST | `/api/v1/categories` | CategoryController |
| PATCH \| DELETE | `/api/v1/categories/{id}` | CategoryController |
| GET \| POST | `/api/v1/cards` | CardController |
| GET \| PUT \| DELETE | `/api/v1/cards/{id}` | CardController |
| GET | `/api/v1/cards/{cardId}/invoices/current` | InvoiceController |
| GET | `/api/v1/cards/{cardId}/invoices/{year}/{month}` | InvoiceController |
| GET | `/api/v1/cards/{cardId}/invoices/timeline` | InvoiceController |
| GET | `/api/v1/cards/{cardId}/invoices/prediction` | InvoiceController |
| POST | `/api/v1/cards/{cardId}/invoices/prediction/refresh` | InvoiceController |
| POST | `/api/v1/invoices/import/preview` | InvoiceImportController (multipart/form-data) |
| POST | `/api/v1/invoices/import` | InvoiceImportController (application/json) |
| GET | `/api/v1/reports/summary?start=&end=` | ReportController |
| GET | `/api/v1/reports/monthly?year=` | ReportController |
| GET | `/api/v1/export/csv?start=&end=` | ReportController (UTF-8 BOM) |
| POST | `/webhook` | TelegramWebhookController |

**Before adding or renaming a route, verify against the controller annotations — this table is hand-maintained.**

## Error envelope

Every error funnels through `interfaces/rest/shared/GlobalExceptionHandler`. All responses use the `ErrorResponse` record (`interfaces/rest/shared/ErrorResponse.java`):

```
{
  "status": 400,
  "error": "Bad Request",
  "message": "human-readable message",
  "timestamp": "2026-04-18T10:00:00",
  "details": { ... }   // optional; validation failures only
}
```

Handles: validation (400), missing/invalid params (400), malformed body (400), access denied (403), not found (404), method not allowed (405), data conflict (409), unsupported media type (415), generic catch-all (500).

## Jackson / JSON conventions

Set in `application.properties`:

- `SNAKE_CASE` property naming (API uses snake_case, Java uses camelCase).
- Non-null default inclusion (omit null fields from responses).
- Dates serialized as ISO-8601 strings (not timestamps).
- Case-insensitive enum deserialization.
- Unknown properties ignored on input.

## Swagger

- `SWAGGER_ENABLED=false` (default) — SpringDoc registers no handlers; `/swagger-ui.html` and `/v3/api-docs` return 404.
- `SWAGGER_ENABLED=true` — spec is publicly accessible without auth. Acceptable for a private single-user app.

## When to update this file

- New REST endpoint → add the row to the REST API table, same PR as the controller change.
- New error type handled by `GlobalExceptionHandler` → extend the handlers list.

## Pointers

- Use cases the controllers invoke: `../application/CLAUDE.md`.
- Security filter ordering and JWT details: `../infrastructure/CLAUDE.md`.
- DTO field shapes that must match the DB: `../infrastructure/` and `../../../resources/db/migration/CLAUDE.md`.
