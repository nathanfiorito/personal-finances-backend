# Diagrama de Arquitetura — FinBot

## Fluxo Principal

```mermaid
flowchart TD
    User([👤 Usuário]) -->|foto / texto / PDF / comando| TG[Telegram]
    TG -->|webhook HTTPS| CF[Cloudflare\nDNS + Proxy + Tunnel]
    CF --> API[FastAPI\nWebhook Handler]

    API --> Router{Router\nTipo de entrada?}

    Router -->|imagem| EXT_IMG[Agente Extrator\nSonnet 4.6 via OpenRouter]
    Router -->|texto| EXT_TXT[Agente Extrator\nHaiku 4.5 via OpenRouter]
    Router -->|PDF com texto| EXT_PDFT[Agente Extrator\nHaiku 4.5 via OpenRouter]
    Router -->|PDF escaneado| EXT_PDFI[Agente Extrator\nSonnet 4.6 via OpenRouter]
    Router -->|comando| CMD[Command Handler\n/relatorio /exportar /categorias]

    EXT_IMG --> CAT[Agente Categorizador\nHaiku 4.5 via OpenRouter]
    EXT_TXT --> CAT
    EXT_PDFT --> CAT
    EXT_PDFI --> CAT

    CAT --> CONFIRM[Confirmação\nInline Keyboard no Telegram]
    CONFIRM -->|✅ Confirmar| DUPCHECK[Verificador de Duplicatas\nHaiku 4.5 via OpenRouter]
    CONFIRM -->|✏️ Editar Categoria| CAT_SEL[Seleção de Categoria\nInline Keyboard]
    CONFIRM -->|❌ Cancelar| DISCARD[Descartado]
    CAT_SEL --> CONFIRM

    DUPCHECK -->|✅ Não duplicata| DB[(Supabase\nPostgreSQL)]
    DUPCHECK -->|⚠️ Duplicata detectada| DUPWARN[Aviso de Duplicata\nInline Keyboard]
    DUPWARN -->|Salvar mesmo assim| DB
    DUPWARN -->|Cancelar| DISCARD

    CMD -->|/relatorio| RPT[Gerador de Relatório]
    CMD -->|/exportar| CSV[Exportador CSV]
    CMD -->|/categorias| CAT_CMD[Gerenciador de Categorias]

    RPT --> DB
    RPT --> LLM_RPT[Sonnet 4.6\nInsight financeiro]
    LLM_RPT --> TG_OUT[Resposta no Telegram]

    CSV --> DB
    CAT_CMD --> DB

    SCHED[APScheduler\nCron — dia 1 às 08h] --> RPT
```

## Visão de Componentes

```mermaid
graph LR
    subgraph "FastAPI App (Monólito Modular)"
        WH[Webhook Handler\nmain.py]
        RT[Router\nhandlers/message.py]
        AG_E[agents/extractor.py]
        AG_C[agents/categorizer.py]
        AG_D[agents/duplicate_checker.py]
        AG_R[agents/reporter.py]
        HDL_CB[handlers/callback.py]
        HDL_CMD[handlers/commands.py]
        SVC_T[services/telegram.py]
        SVC_L[services/llm.py]
        SVC_D[services/database.py]
        MDL_E[models/expense.py]
        MDL_P[models/pending.py]
        SCHED[scheduler/reports.py]
    end

    subgraph "Externos"
        TG_API[Telegram Bot API]
        OR_API[OpenRouter API\nSonnet 4.6 + Haiku 4.5]
        SB_API[Supabase PostgreSQL]
    end

    WH --> RT
    RT --> AG_E
    RT --> HDL_CB
    RT --> HDL_CMD
    HDL_CB --> AG_D
    HDL_CB --> SVC_D
    HDL_CMD --> AG_R
    HDL_CMD --> SVC_D
    AG_E --> SVC_L
    AG_C --> SVC_L
    AG_D --> SVC_L
    AG_R --> SVC_L
    AG_R --> SVC_D
    AG_C --> SVC_D
    SVC_L --> OR_API
    SVC_D --> SB_API
    SVC_T --> TG_API
    AG_E --> MDL_E
    HDL_CB --> MDL_P
    RT --> MDL_P
    SCHED --> AG_R
```

## Fluxo de Dados — Registro de Despesa (Imagem)

```mermaid
sequenceDiagram
    participant U as Usuário
    participant T as Telegram
    participant F as FastAPI
    participant OR as OpenRouter
    participant DB as Supabase

    U->>T: Envia foto de comprovante
    T->>F: Webhook (POST /webhook)
    F->>T: getFile (download da imagem)
    T-->>F: Bytes da imagem

    F->>OR: Sonnet 4.6 + imagem (extração)
    OR-->>F: JSON {valor, data, estabelecimento, cnpj, confiança}

    F->>DB: get_active_categories() (cache 5min)
    DB-->>F: ["Alimentação", "Transporte", ...]

    F->>OR: Haiku 4.5 (categorização)
    OR-->>F: "Alimentação"

    F->>T: sendMessage + Inline Keyboard [Confirmar][Categoria][Cancelar]
    T->>U: "R$ 45,90 - Supermercado - Alimentação\n[Confirmar][Categoria][Cancelar]"

    U->>T: Clica Confirmar
    T->>F: Callback Query (confirm)

    F->>DB: get_recent_expenses(limit=3)
    DB-->>F: [últimas 3 despesas]

    F->>OR: Haiku 4.5 (verificação de duplicatas)
    OR-->>F: "OK"

    F->>DB: save_expense(expense, categoria)
    DB-->>F: UUID da despesa

    F->>T: editMessage "Despesa de R$ 45,90 em Alimentação registrada!"
    T->>U: Confirmação final
```

## Inline Keyboards

### Confirmação (após extração)
```
[ Confirmar ] [ Categoria ] [ Cancelar ]
```

### Aviso de Duplicata (após detect)
```
[ Salvar mesmo assim ] [ Cancelar ]
```

### Seleção de Categoria (ao clicar "Categoria")
```
[ Alimentação  ] [ Transporte ]
[ Moradia      ] [ Saúde      ]
[ Educação     ] [ Lazer      ]
[ Vestuário    ] [ Serviços   ]
[ Pets         ] [ Outros     ]
```
*(mais categorias customizadas adicionadas pelo usuário)*
