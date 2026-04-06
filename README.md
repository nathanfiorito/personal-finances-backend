# FinBot — Bot de Controle de Despesas no Telegram

Bot pessoal no Telegram para registro e categorização automática de despesas usando agentes de IA.

## O que faz

- Recebe comprovantes de pagamento (foto), notas fiscais (PDF) ou texto livre via Telegram
- Extrai automaticamente: valor, data, estabelecimento, descrição
- Categoriza a despesa com IA (Alimentação, Transporte, Saúde, etc.)
- Pede confirmação antes de salvar
- Gera relatórios financeiros por período

## Stack

| Componente | Tecnologia |
|---|---|
| Backend | Python 3.12+ / FastAPI |
| Bot | python-telegram-bot |
| LLM | Claude Sonnet 4.6 + Haiku 4.5 via OpenRouter |
| Banco de Dados | PostgreSQL (Supabase) |
| Infra | Render (hosting) + Cloudflare (DNS/Tunnel) |

## Estrutura do Projeto

```
finbot/
├── src/
│   ├── agents/               # Agentes de IA
│   │   ├── __init__.py
│   │   ├── extractor.py      # Agente Extrator (visão + texto)
│   │   ├── categorizer.py    # Agente Categorizador
│   │   └── reporter.py       # Agente de Relatórios
│   ├── services/             # Serviços externos
│   │   ├── __init__.py
│   │   ├── telegram.py       # Telegram Bot API wrapper
│   │   ├── llm.py            # OpenRouter client
│   │   └── database.py       # Supabase client
│   ├── models/               # Modelos de dados
│   │   ├── __init__.py
│   │   └── expense.py        # Pydantic models (Expense, Category, etc.)
│   ├── handlers/             # Handlers do Telegram
│   │   ├── __init__.py
│   │   ├── message.py        # Handler de mensagens (foto/texto)
│   │   ├── callback.py       # Handler de callbacks (inline keyboards)
│   │   └── commands.py       # Handler de comandos (/relatorio, /start, etc.)
│   ├── config/               # Configuração
│   │   ├── __init__.py
│   │   └── settings.py       # Pydantic Settings (env vars)
│   ├── scheduler/            # Tarefas agendadas
│   │   ├── __init__.py
│   │   └── reports.py        # Cron de relatório mensal
│   └── main.py               # Entrypoint FastAPI + webhook setup
├── tests/
│   ├── test_extractor.py
│   ├── test_categorizer.py
│   └── test_models.py
├── docs/
│   ├── ARCHITECTURE.md
│   ├── ARCHITECTURE-DIAGRAM.md
│   ├── POC.md
│   ├── MVP-ROADMAP.md
│   ├── INFRA-COSTS.md
│   └── SECURITY-CHECKLIST.md
├── .env.example
├── .gitignore
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
| `/relatorio semana` | Relatório dos últimos 7 dias |
| `/relatorio mes` | Relatório do mês corrente |
| `/categorias` | Listar categorias disponíveis (Pós-MVP) |
| `/ajuda` | Lista de comandos disponíveis |

## Documentação

- [Arquitetura](docs/ARCHITECTURE.md)
- [Diagramas](docs/ARCHITECTURE-DIAGRAM.md)
- [POC](docs/POC.md)
- [MVP Roadmap](docs/MVP-ROADMAP.md)
- [Custos de Infra](docs/INFRA-COSTS.md)
- [Checklist de Segurança](docs/SECURITY-CHECKLIST.md)

## Licença

Projeto pessoal — uso privado.
