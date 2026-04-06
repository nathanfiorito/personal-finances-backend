# POC-01 — Setup do Projeto

**Fase:** POC | **Dias:** 1–2 | **Prioridade:** Must-have

## Objetivo

Estruturar o repositório, configurar o ambiente de desenvolvimento e validar a comunicação básica entre Telegram e o servidor local via Cloudflare Tunnel.

## Tarefas

- [ X ] Criar estrutura de pastas conforme definida no README (`src/agents`, `src/services`, `src/handlers`, `src/models`, `src/config`, `tests/`)
- [ X ] Configurar `pyproject.toml` com metadados do projeto e dependências de dev
- [ X ] Criar `requirements.txt` com dependências principais:
  - `fastapi`, `uvicorn`
  - `python-telegram-bot`
  - `openai` (SDK compatível com OpenRouter)
  - `pydantic`, `pydantic-settings`
  - `httpx`
- [ X ] Criar `src/config/settings.py` com Pydantic Settings lendo variáveis de ambiente
- [ X ] Criar `.env.example` com todas as chaves necessárias (sem valores)
- [ X ] Criar `src/main.py` com app FastAPI mínima e endpoint `/webhook`
- [ X ] Verificar que `/webhook` recebe POST do Telegram e loga o payload
- [ X ] Configurar Cloudflare Tunnel apontando para `localhost:8000`
- [ X ] Registrar webhook no Telegram via API e confirmar recebimento de mensagens no log
- [ X ] Adicionar `Dockerfile` básico para futura containerização

## Critérios de Aceite

- `uvicorn src.main:app --reload` sobe sem erros
- Mensagem enviada no Telegram aparece logada no terminal
- `.env` não está no git (verificar `.gitignore`)

## Variáveis de Ambiente Necessárias

```env
TELEGRAM_BOT_TOKEN=
TELEGRAM_WEBHOOK_SECRET=
TELEGRAM_ALLOWED_CHAT_ID=
OPENROUTER_API_KEY=
```

## Dependências

Nenhuma — tarefa inicial.
