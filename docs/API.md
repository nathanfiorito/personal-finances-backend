# API Reference — Personal Finances

Reference for frontend development. Covers HTTP endpoints, data models, and Telegram bot commands.

---

## HTTP Endpoints

### `GET /health`

Application health check.

**Response `200 OK`:**
```json
{ "status": "ok" }
```

---

### `POST /webhook`

Receives Telegram updates. Used exclusively by the Telegram Bot API.

**Required header:**
```
X-Telegram-Bot-Api-Secret-Token: <TELEGRAM_WEBHOOK_SECRET>
```

**Response `200 OK`:** `{ "ok": true }`
**Response `403 Forbidden`:** invalid token
**Rate limit:** 30 req/min per IP

---

## REST API — Frontend (`/api/v2/...`)

All `/api/v2/*` routes require **Supabase Auth JWT** authentication:

```
Authorization: Bearer <jwt>
```

| Code | Situation |
|---|---|
| `401` | Header missing, malformed, or invalid token |
| `403` | Token expired |

**CORS:** accepts origins matching `*.nathanfiorito.com.br` with methods `GET, POST, PUT, PATCH, DELETE`.

---

### Transactions — `src/v2/adapters/primary/bff/routers/transactions.py`

#### `POST /api/v2/transactions`

Creates a transaction manually (no AI extraction).

**Body:**
```json
{
  "amount": "50.00",
  "date": "2025-01-15",
  "establishment": "Mercado",
  "description": "Compras",
  "category_id": 1,
  "tax_id": null,
  "entry_type": "text",
  "transaction_type": "expense"
}
```

**Response `201 Created`:** `Transaction`

---

#### `PUT /api/v2/transactions/{id}`

Replaces a transaction (full update). Unset fields keep their previous values.

**Body:** same shape as `POST /api/v2/transactions` (all fields optional)
**Response `200 OK`:** updated `Transaction`
**Response `404`:** not found

---

#### `DELETE /api/v2/transactions/{id}`

Deletes a transaction.

**Response `204 No Content`**
**Response `404`:** not found

---

### Categories — `src/v2/adapters/primary/bff/routers/categories.py`

#### `GET /api/v2/categories`

List active categories (`is_active = true`).

**Response `200 OK`:**
```json
[{ "id": 1, "name": "Alimentação", "is_active": true }]
```

---

#### `POST /api/v2/categories`

Create a new category.

**Body:** `{ "name": "Nova Categoria" }`
**Response `201 Created`:** `Category`
**Response `409 Conflict`:** duplicate name

---

#### `PATCH /api/v2/categories/{id}`

Partial update — rename and/or activate/deactivate.

**Body:** `{ "name"?: str, "is_active"?: bool }`
**Response `200 OK`:** updated `Category`
**Response `404`:** not found

---

#### `DELETE /api/v2/categories/{id}`

Deactivates a category (`is_active = false`). Does not delete the record.

**Response `204 No Content`**
**Response `404`:** not found

---

### Reports — `src/v2/adapters/primary/bff/routers/reports.py`

#### `GET /api/v2/reports/monthly`

Monthly breakdown — only returns months with at least one transaction.

**Query params:** `year` (int, default: current year)

**Response `200 OK`:**
```json
[
  {
    "month": 1,
    "total": "369.40",
    "by_category": [
      { "category": "Alimentação", "total": "245.90" }
    ]
  }
]
```

---

### Export — `src/v2/adapters/primary/bff/routers/export.py`

#### `GET /api/v2/export/csv`

Export transactions for a period as a CSV file.

**Required query params:** `start`, `end` (`YYYY-MM-DD`)

**Response `200 OK`:** CSV file with header:
```
id,date,establishment,description,category,amount,tax_id,entry_type,confidence,created_at
```

**Response header:**
```
Content-Disposition: attachment; filename=expenses_<start>_<end>.csv
```

---

### BFF — Page Endpoints — `src/v2/adapters/primary/bff/routers/bff_dashboard.py`, `bff_expenses.py`

These endpoints aggregate data for a specific frontend page in a single request.

#### `GET /api/v2/bff/dashboard`

Returns everything the Dashboard page needs in one call.

**Required query params:** `start`, `end` (`YYYY-MM-DD`)

**Response `200 OK`:**
```json
{
  "expense_summary": [{ "category": "Alimentação", "total": "245.90" }],
  "income_summary":  [{ "category": "Salário",     "total": "5000.00" }],
  "transaction_count": 42
}
```

**Response `422`:** `start > end`

---

#### `GET /api/v2/bff/expenses`

Returns paginated transactions and the full active category list for the Expenses page.

**Query params:** `start`, `end`, `category_id`, `transaction_type` (`"income" | "expense"`), `page` (default `1`), `page_size` (default `20`, max `100`)

**Response `200 OK`:**
```json
{
  "transactions": { "items": [...], "total": 42, "page": 1, "page_size": 20 },
  "categories":   [{ "id": 1, "name": "Alimentação", "is_active": true }]
}
```

---

#### `GET /api/v2/bff/reports`

Returns combined income + expense monthly totals for the Reports page.

**Query params:** `year` (int, required)

**Response `200 OK`:**
```json
[
  {
    "month": 1,
    "income_total": "5000.00",
    "expense_total": "369.40",
    "expense_by_category": [
      { "category": "Alimentação", "total": "245.90" }
    ]
  }
]
```

Only months with at least one transaction (income or expense) are returned.

---

## Data Models

### `Transaction` — persisted expense

```python
@dataclass
class Expense:   # Domain entity; serialized as Transaction in API
    id: str
    amount: Decimal
    date: date
    establishment: str | None
    description: str | None
    category: str        # category name (via join)
    category_id: int | None
    tax_id: str | None
    entry_type: str      # "image" | "text" | "pdf"
    transaction_type: str  # "expense" | "income"
    confidence: float | None
    created_at: datetime
```

### `Category`

```python
@dataclass
class Category:
    id: int
    name: str
    is_active: bool
```

---

## Telegram Bot Commands

| Command | Parameters | Behavior | Default period |
|---|---|---|---|
| `/start` | — | Welcome message | — |
| `/ajuda` | — | List all commands | — |
| `/relatorio` | `[period]` | HTML report with category breakdown + AI insight | current month |
| `/exportar` | `[period]` | CSV file of transactions | current month |
| `/categorias` | — | List active categories | — |
| `/categorias add <name>` | `<name>` | Add a new category | — |

**Period formats:**
| Token | Range |
|---|---|
| *(empty)* or `mes` | 1st of current month to today |
| `semana` | last 7 days |
| `anterior` | previous full month |
| `MM/AAAA` | specific month (e.g. `03/2025`) |

---

## Inline Keyboard Callbacks

| `callback_data` | Action |
|---|---|
| `confirm` | Run duplicate check, then save expense |
| `force_confirm` | Save without duplicate check |
| `cancel` | Discard pending expense |
| `edit_category` | Show category selection keyboard |
| `set_category:<id>:<name>` | Update pending expense category, return to confirmation |

---

## Report Output Format

The `/relatorio` command returns Telegram HTML (`parse_mode=HTML`):

```
📊 Report — <period>

💰 Total: R$ 1.234,56
📦 <N> transactions

By category:
🍽️ Alimentação: R$ 456,78 (37%)
🚗 Transporte: R$ 234,56 (19%)
...

🏪 Top establishments:
• Mercado Extra (5x)
• Shell (3x)
• iFood (2x)

💡 <2-sentence insight from Sonnet 4.6>
```

---

## CSV Output Format

The `/exportar` command generates a UTF-8 BOM CSV (Excel-compatible).

**Header:**
```
date,amount,establishment,category,description,tax_id,entry_type
```

**Filename:** `despesas_YYYY-MM-DD_YYYY-MM-DD.csv`

---

## Pending State (Telegram Bot)

Between extraction and user confirmation, the pending expense is held in memory:

- One pending expense per `chat_id` at a time
- Automatically expires after 10 minutes
- Cleared on confirm, cancel, or timeout
- Implemented by `InMemoryPendingStateAdapter` (`src/v2/adapters/secondary/memory/`)

---

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `TELEGRAM_BOT_TOKEN` | Yes | — | Bot token from @BotFather |
| `TELEGRAM_WEBHOOK_SECRET` | Yes | — | Secret to validate webhook requests |
| `TELEGRAM_ALLOWED_CHAT_ID` | Yes | — | Authorized user's chat_id |
| `OPENROUTER_API_KEY` | Yes | — | OpenRouter API key |
| `OPENROUTER_BASE_URL` | No | `https://openrouter.ai/api/v1` | OpenRouter base URL |
| `MODEL_VISION` | No | `anthropic/claude-sonnet-4-6` | Model for vision + reports |
| `MODEL_FAST` | No | `anthropic/claude-haiku-4-5` | Model for text + categorization |
| `SUPABASE_URL` | Yes | — | Supabase project URL |
| `SUPABASE_SERVICE_KEY` | Yes | — | Supabase service role key |
| `SIGNOZ_OTLP_ENDPOINT` | No | — | SigNoz OTLP endpoint for observability |
| `OTEL_SERVICE_NAME` | No | `personal-finances` | Service name for OTLP traces |
