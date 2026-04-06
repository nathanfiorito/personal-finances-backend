# FinBot — Bot de Controle de Despesas no Telegram

Bot pessoal no Telegram para registro e categorização automática de despesas usando agentes de IA.

## O que faz

- Recebe comprovantes de pagamento (foto), notas fiscais (PDF) ou texto livre via Telegram
- Extrai automaticamente: valor, data, estabelecimento, descrição
- Categoriza a despesa com IA (Alimentação, Transporte, Saúde, etc.)
- Detecta possíveis despesas duplicadas antes de salvar
- Pede confirmação antes de salvar (permite editar a categoria)
- Gera relatórios financeiros por período
- Exporta despesas em CSV

## Stack

| Componente | Tecnologia |
|---|---|
| Backend | Python 3.12+ / FastAPI |
| Bot | httpx (HTTP direto para Telegram Bot API, webhook mode) |
| LLM | Claude Sonnet 4.6 + Haiku 4.5 via OpenRouter |
| Banco de Dados | PostgreSQL (Supabase) |
| Infra | Render (hosting) + Cloudflare (DNS/Tunnel) |

## Estrutura do Projeto

```
telegram-finances/
├── src/
│   ├── agents/               # Agentes de IA
│   │   ├── extractor.py      # Extrai dados de imagens, PDFs e texto
│   │   ├── categorizer.py    # Classifica despesa em categoria
│   │   ├── duplicate_checker.py  # Detecta possíveis duplicatas via LLM
│   │   └── reporter.py       # Gera relatórios financeiros
│   ├── services/             # Serviços externos
│   │   ├── telegram.py       # Telegram Bot API wrapper (httpx)
│   │   ├── llm.py            # OpenRouter client com retry
│   │   └── database.py       # Supabase client
│   ├── models/               # Modelos de dados
│   │   ├── expense.py        # Pydantic models (ExtractedExpense, Expense)
│   │   └── pending.py        # Store in-memory de despesas pendentes (TTL 10min)
│   ├── handlers/             # Handlers do Telegram
│   │   ├── message.py        # Router principal (foto/texto/PDF/comando)
│   │   ├── callback.py       # Callbacks de inline keyboards
│   │   └── commands.py       # Comandos (/relatorio, /exportar, /categorias, etc.)
│   ├── config/
│   │   └── settings.py       # Pydantic Settings (env vars)
│   ├── scheduler/
│   │   └── reports.py        # Cron de relatório mensal (APScheduler)
│   └── main.py               # Entrypoint FastAPI + webhook
├── tests/
│   ├── conftest.py
│   ├── test_extractor.py
│   ├── test_categorizer.py
│   ├── test_duplicate_checker.py
│   ├── test_reporter.py
│   ├── test_database.py
│   ├── test_callback.py
│   ├── test_commands.py
│   ├── test_scheduler.py
│   └── test_webhook.py
├── docs/
│   ├── API.md                # Referência de API, dados e banco (para frontend)
│   ├── ARCHITECTURE.md
│   ├── ARCHITECTURE-DIAGRAM.md
│   ├── MVP-ROADMAP.md
│   ├── INFRA-COSTS.md
│   ├── SECURITY-CHECKLIST.md
│   ├── POC.md
│   └── supabase_schema.sql
├── .env.example
├── requirements.txt
├── pyproject.toml
├── Dockerfile
└── README.md
```

## Setup Local

### Pré-requisitos

- Python 3.12+
- Conta no Telegram (para criar o bot via @BotFather)
- Conta na OpenRouter (para API key)
- Conta no Supabase (para banco de dados)
- Cloudflare Tunnel instalado (`cloudflared`)

### Instalação

```bash
# Clonar o repositório
git clone https://github.com/seu-usuario/finbot.git
cd finbot

# Criar virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Instalar dependências
pip install -r requirements.txt

# Copiar e configurar variáveis de ambiente
cp .env.example .env
# Editar .env com suas chaves
```

### Configurar o Telegram Bot

1. Falar com @BotFather no Telegram
2. Criar novo bot: `/newbot`
3. Copiar o token para `.env` → `TELEGRAM_BOT_TOKEN`
4. Obter seu chat_id (enviar mensagem para @userinfobot) → `TELEGRAM_ALLOWED_CHAT_ID`

### Rodar em Dev (com Cloudflare Tunnel)

```bash
# Terminal 1 — Subir o FastAPI
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2 — Criar túnel Cloudflare
cloudflared tunnel --url http://localhost:8000
# Copiar a URL gerada (ex: https://xyz.trycloudflare.com)

# Terminal 3 — Registrar webhook no Telegram
curl -X POST "https://api.telegram.org/bot<TOKEN>/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://xyz.trycloudflare.com/webhook", "secret_token": "<SEU_SECRET>"}'
```

## Comandos do Bot

| Comando | Descrição |
|---|---|
| `/start` | Mensagem de boas-vindas |
| `/ajuda` | Lista de comandos disponíveis |
| `/relatorio` | Relatório do mês corrente |
| `/relatorio semana` | Relatório dos últimos 7 dias |
| `/relatorio anterior` | Relatório do mês anterior |
| `/relatorio MM/AAAA` | Relatório de mês específico (ex: `03/2025`) |
| `/exportar` | Exportar despesas do mês corrente como CSV |
| `/exportar anterior` | CSV do mês anterior |
| `/exportar MM/AAAA` | CSV de mês específico |
| `/categorias` | Listar categorias ativas |
| `/categorias add <nome>` | Adicionar nova categoria |

## Documentação

- [API Reference](docs/API.md) — endpoints, modelos de dados e schema do banco (referência para frontend)
- [Arquitetura](docs/ARCHITECTURE.md)
- [Diagramas](docs/ARCHITECTURE-DIAGRAM.md)
- [MVP Roadmap](docs/MVP-ROADMAP.md)
- [Custos de Infra](docs/INFRA-COSTS.md)
- [Checklist de Segurança](docs/SECURITY-CHECKLIST.md)
- [POC](docs/POC.md)

## Licença

Projeto pessoal — uso privado.
