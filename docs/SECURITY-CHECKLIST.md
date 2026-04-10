# Checklist de Segurança — Personal Finances

## Base (Obrigatório)

- [ ] Variáveis de ambiente nunca commitadas (`.env` no `.gitignore`)
- [ ] `.env.example` com as chaves necessárias (sem valores reais)
- [ ] HTTPS obrigatório em produção (Cloudflare garante isso)
- [ ] Inputs do usuário sempre validados/sanitizados
- [ ] Dependências auditadas periodicamente (`pip audit`)

## Python / FastAPI

- [ ] Pydantic models para validação de entrada em todos os endpoints
- [ ] Rate limiting configurado no webhook (`slowapi` — 30/min no webhook, 60/min global)
- [ ] CORS restrito (neste caso, apenas Telegram precisa acessar o webhook)
- [ ] Secrets via variáveis de ambiente — nunca hardcoded
- [ ] Webhook validado com secret token do Telegram (`X-Telegram-Bot-Api-Secret-Token`)
- [ ] Logs sem dados sensíveis (não logar tokens, API keys ou dados financeiros completos)

## Telegram Bot

- [ ] Bot token armazenado exclusivamente em variável de ambiente
- [ ] Webhook configurado com `secret_token` para validar origem das requests
- [ ] Comandos administrativos protegidos por `chat_id` (aceitar apenas do seu usuário)
- [ ] Não expor informações sensíveis nas mensagens do bot (mascarar CNPJ, valores parciais)

## OpenRouter / LLM

- [ ] API key da OpenRouter em variável de ambiente
- [ ] Não enviar dados pessoais desnecessários nos prompts (minimalismo)
- [ ] Validar respostas do LLM antes de persistir (schema validation com Pydantic)
- [ ] Timeout configurado nas chamadas de API (30s — evitar hang)
- [ ] Retry com backoff exponencial para falhas transitórias (3 tentativas: 1s, 2s, 4s)

## Supabase / Banco de Dados

- [ ] Connection string em variável de ambiente (`SUPABASE_SERVICE_KEY`)
- [ ] Row Level Security (RLS) habilitado mesmo para single-user (boa prática)
- [ ] Queries parametrizadas (SDK Supabase — nunca string concatenation)
- [ ] Backups regulares dos dados (export manual periódico no free tier)

## Cloudflare

- [ ] Tunnel configurado sem expor portas desnecessárias
- [ ] DNS com proxy ativado (ocultar IP real do servidor)
- [ ] WAF rules básicas habilitadas (free tier inclui proteção DDoS)

## Variáveis de Ambiente Necessárias

```env
# .env.example
TELEGRAM_BOT_TOKEN=
TELEGRAM_WEBHOOK_SECRET=
TELEGRAM_ALLOWED_CHAT_ID=
OPENROUTER_API_KEY=
SUPABASE_URL=
SUPABASE_SERVICE_KEY=
```
