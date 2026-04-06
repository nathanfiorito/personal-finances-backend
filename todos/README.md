# FinBot — Backlog de Tarefas

Organizado em duas fases: **POC** (validação técnica) e **MVP** (produto funcional).

---

## Fase 1 — POC

Objetivo: validar extração de dados de comprovantes com Claude Sonnet 4.6 via OpenRouter. Prazo: 10 dias úteis.

| # | Tarefa | Status |
|---|---|---|
| 1 | [Setup do projeto](./poc/01-setup.md) | ✅ |
| 2 | [Integração OpenRouter + prompt engineering](./poc/02-integracao-llm.md) | ✅ |
| 3 | [Testes de acurácia com comprovantes reais](./poc/03-testes-acuracia.md) | ⬜ |
| 4 | [Relatório de resultados e decisão go/no-go](./poc/04-go-nogo.md) | ⬜ |

---

## Fase 2 — MVP

### Must-have

| # | Tarefa | Status |
|---|---|---|
| M1 | [Webhook Telegram (receber foto/texto)](./mvp/must/01-webhook-telegram.md) | ✅ |
| M2 | [Agente Extrator](./mvp/must/02-agente-extrator.md) | ✅ |
| M3 | [Agente Categorizador](./mvp/must/03-agente-categorizador.md) | ✅ |
| M4 | [Fluxo de confirmação (inline keyboards)](./mvp/must/04-fluxo-confirmacao.md) | ✅ |
| M5 | [Persistência no Supabase](./mvp/must/05-persistencia.md) | ✅ |

### Should-have

| # | Tarefa | Status |
|---|---|---|
| S1 | [Comando /relatorio](./mvp/should/06-comando-relatorio.md) | ✅ |
| S2 | [Scheduler de relatório mensal automático](./mvp/should/07-scheduler-mensal.md) | ✅ |
| S3 | [Suporte a PDF de NF-e](./mvp/should/08-suporte-pdf.md) | ✅ |

### Could-have (Pós-MVP)

| # | Tarefa | Status |
|---|---|---|
| C1 | [Comando /categorias](./mvp/could/09-comando-categorias.md) | ⬜ |
| C2 | [Exportação CSV/Excel](./mvp/could/10-exportacao-csv.md) | ⬜ |

---

## Legenda

| Símbolo | Significado |
|---|---|
| ⬜ | Não iniciado |
| 🔄 | Em progresso |
| ✅ | Concluído |
| 🚫 | Bloqueado |
