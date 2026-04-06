# MVP-S2 — Scheduler de Relatório Mensal Automático

**Fase:** MVP | **Estimativa:** 1 dia | **Prioridade:** Should-have

## Objetivo

Disparar automaticamente o relatório do mês anterior no dia 1 de cada mês às 08:00, sem intervenção manual.

## Tarefas

### Scheduler (`src/scheduler/reports.py`)

- [ X ] Configurar APScheduler com job:
  - Cron: `0 8 1 * *` (08:00 no dia 1 de cada mês)
  - Timezone: `America/Sao_Paulo`
  - Job: `send_monthly_report()`

- [ X ] `send_monthly_report()`:
  1. Calcular período: primeiro e último dia do mês anterior
  2. Chamar `reporter.generate_report(start, end)`
  3. Enviar mensagem via `telegram_client.send_message(TELEGRAM_ALLOWED_CHAT_ID, report)`
  4. Log do envio bem-sucedido

### Integração com FastAPI (`src/main.py`)

- [ X ] Iniciar o scheduler junto com o app FastAPI (`startup` event)
- [ X ] Desligar o scheduler no `shutdown` event

### Serviço Telegram (`src/services/telegram.py`)

- [ X ] `send_message(chat_id: int, text: str)` — para envio proativo (sem resposta a update)

### Testes

- [ X ] Testar que o job é registrado na inicialização do app
- [ X ] Testar `send_monthly_report()` com DB mockado (verificar que envia mensagem correta)
- [ X ] Testar cálculo de período (mês anterior ao dia 1)

## Critérios de Aceite

- Scheduler inicia junto com o FastAPI sem bloquear o servidor
- Job cron configurado para `America/Sao_Paulo`
- Mensagem proativa chega ao Telegram no primeiro dia do mês
- Falha no scheduler não derruba o servidor (exceção capturada com log)

## Dependências

- MVP-S1 (comando /relatorio) — reutiliza `reporter.generate_report()`
- MVP-M5 (persistência) — para consultar despesas do mês anterior
