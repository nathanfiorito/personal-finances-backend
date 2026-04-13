# Architecture Diagram — Personal Finances

## Main Flow (Telegram Bot)

```mermaid
flowchart TD
    User([👤 User]) -->|photo / text / PDF / command| TG[Telegram]
    TG -->|webhook HTTPS| CF[Cloudflare\nDNS + Proxy + Tunnel]
    CF --> API[FastAPI\nWebhook Handler]

    API --> WHOOK{Webhook Router\nv2 primary adapter}

    WHOOK -->|image / text / PDF| MSG[ProcessMessage\nuse case]
    WHOOK -->|/command| CMD[Command Handler\n/relatorio /exportar /categorias]
    WHOOK -->|callback_query| CB[Callback Handler\nconfirm / cancel / edit_category]

    MSG --> LLM[LLMPort\nextract_expense\nSonnet 4.6 or Haiku 4.5]
    LLM --> PENDING[InMemoryPendingStateAdapter\nTTL 10 min]
    PENDING --> CONFIRM[Confirmation\nTelegram Inline Keyboard]

    CB -->|confirm| DUPCHECK[LLMPort\ncheck_duplicate\nHaiku 4.5]
    CB -->|set_category| PENDING
    CB -->|cancel| DISCARD[Discarded]

    DUPCHECK -->|no duplicate| REPO[(SupabaseExpenseRepository\nPostgreSQL)]
    DUPCHECK -->|duplicate warning| DUPWARN[Duplicate Warning\nInline Keyboard]
    DUPWARN -->|force_confirm| REPO
    DUPWARN -->|cancel| DISCARD

    CMD -->|/relatorio| RPT[GenerateTelegramReport\nuse case]
    CMD -->|/exportar| CSV[ExportCsv use case]
    CMD -->|/categorias| CAT_CMD[ListCategories / CreateCategory\nuse cases]

    RPT --> REPO
    RPT --> LLM_RPT[LLMPort\ngenerate_report_insight\nSonnet 4.6]
    LLM_RPT --> NOTIFIER[TelegramNotifierAdapter]

    CSV --> REPO
    CAT_CMD --> CATREPO[(SupabaseCategoryRepository)]

    SCHED[APScheduler\nCron — 1st at 08:00 BRT] --> RPT
```

## Hexagonal Architecture — Component View

```mermaid
graph LR
    subgraph "Primary Adapters"
        BFF["BFF REST API\n/api/v2/...\nbff/routers/*.py"]
        TGWHOOK["Telegram Webhook\ntelegram/webhook.py\n+ handlers/"]
    end

    subgraph "Domain"
        UC_E["Expense Use Cases\ncreate, list, get, update, delete"]
        UC_C["Category Use Cases\nlist, create, update, deactivate"]
        UC_R["Report Use Cases\nsummary, monthly, export_csv"]
        UC_T["Telegram Use Cases\nprocess, confirm, cancel, change_category, report"]
        PORTS["Ports (ABCs)\nExpenseRepository\nCategoryRepository\nLLMPort\nNotifierPort\nPendingStatePort"]
    end

    subgraph "Secondary Adapters"
        SBREPO["SupabaseExpenseRepository\nSupabaseCategoryRepository"]
        LLMADP["OpenRouterLLMAdapter\nvia services/llm.py"]
        NOTADP["TelegramNotifierAdapter\nvia services/telegram.py"]
        MEMADP["InMemoryPendingStateAdapter\nTTL dict"]
    end

    subgraph "External Services"
        TG_API[Telegram Bot API]
        OR_API[OpenRouter API\nSonnet 4.6 + Haiku 4.5]
        SB_API[Supabase PostgreSQL]
    end

    BFF --> UC_E & UC_C & UC_R
    TGWHOOK --> UC_T
    UC_E & UC_C & UC_R & UC_T --> PORTS
    PORTS -.->|implemented by| SBREPO & LLMADP & NOTADP & MEMADP
    SBREPO --> SB_API
    LLMADP --> OR_API
    NOTADP --> TG_API
```

## Sequence — Expense Registration (Image)

```mermaid
sequenceDiagram
    participant U as User
    participant T as Telegram
    participant F as FastAPI + v2
    participant OR as OpenRouter
    participant DB as Supabase

    U->>T: Sends receipt photo
    T->>F: Webhook (POST /webhook)
    F->>T: getFile (download image)
    T-->>F: Image bytes

    F->>OR: Sonnet 4.6 + image (extraction)
    OR-->>F: JSON {amount, date, establishment, tax_id, transaction_type, confidence}

    F->>DB: list active categories
    DB-->>F: ["Alimentação", "Transporte", ...]

    F->>OR: Haiku 4.5 (categorize)
    OR-->>F: "Alimentação"

    F->>T: sendMessage + Inline Keyboard [Confirm][Category][Cancel]
    T->>U: "R$ 45,90 - Supermercado - Alimentação\n[Confirm][Category][Cancel]"

    U->>T: Clicks Confirm
    T->>F: Callback Query (confirm)

    F->>DB: list recent expenses (limit=3)
    DB-->>F: [last 3 expenses]

    F->>OR: Haiku 4.5 (duplicate check)
    OR-->>F: "OK"

    F->>DB: save expense
    DB-->>F: expense UUID

    F->>T: editMessage "Despesa de R$ 45,90 em Alimentação registrada!"
    T->>U: Final confirmation
```

## Inline Keyboards

### Confirmation (after extraction)
```
[ ✅ Confirm ] [ ✏️ Category ] [ ❌ Cancel ]
```

### Duplicate Warning
```
[ 💾 Save anyway ] [ ❌ Cancel ]
```

### Category Selection (after clicking "Category")
```
[ Alimentação  ] [ Transporte ]
[ Moradia      ] [ Saúde      ]
[ Educação     ] [ Lazer      ]
[ Vestuário    ] [ Serviços   ]
[ Pets         ] [ Outros     ]
```
*(plus any custom categories added by the user)*
