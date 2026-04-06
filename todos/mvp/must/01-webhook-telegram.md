# MVP-M1 — Webhook Telegram (receber foto/texto/PDF)

**Fase:** MVP | **Estimativa:** 2 dias | **Prioridade:** Must-have

## Objetivo

Implementar o gateway de entrada completo: receber mensagens do Telegram (fotos, textos e PDFs), validar a origem via `secret_token`, restringir acesso ao `chat_id` autorizado e rotear para o handler correto.

## Tarefas

### Segurança do Webhook

- [ X ] Validar header `X-Telegram-Bot-Api-Secret-Token` em toda request ao `/webhook`
- [ X ] Rejeitar com 403 qualquer request sem o token ou com token inválido
- [ X ] Verificar `chat_id` em todo update — ignorar silenciosamente mensagens de outros usuários
- [ X ] Rate limiting via `slowapi` (ex: 30 req/min por IP)

### Roteamento (`src/handlers/message.py`)

- [ X ] Identificar tipo do update:
  - `message.photo` → imagem
  - `message.document` com `mime_type == "application/pdf"` → PDF
  - `message.text` que não começa com `/` → texto livre
  - `message.text` que começa com `/` → delegar aos handlers de comando
- [ X ] Responder imediatamente com "Processando..." enquanto o agente roda (evita timeout do Telegram)
- [ X ] Baixar arquivo de foto via Telegram File API (pegar `file_id` da maior resolução)

### Handlers de Comando (`src/handlers/commands.py`)

- [ X ] `/start` — mensagem de boas-vindas
- [ X ] `/ajuda` — lista de comandos disponíveis

### Testes

- [ X ] `tests/test_webhook.py`: testar roteamento correto para cada tipo de mensagem
- [ X ] Testar rejeição de requests sem secret_token
- [ X ] Testar rejeição de chat_id não autorizado

## Critérios de Aceite

- Foto, texto e PDF chegam ao handler correto
- Requests sem token retornam 403
- Mensagens de outro `chat_id` são ignoradas sem erro

## Dependências

- POC-01 (setup) concluído
- Variáveis `TELEGRAM_BOT_TOKEN`, `TELEGRAM_WEBHOOK_SECRET`, `TELEGRAM_ALLOWED_CHAT_ID` configuradas
