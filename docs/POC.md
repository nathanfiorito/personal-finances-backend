# POC — Personal Finances (Bot de Despesas no Telegram)

## Objetivo

Validar que o **Claude Sonnet 4.6 via OpenRouter** consegue extrair dados estruturados (valor, data, estabelecimento, descrição) de fotos de comprovantes de pagamento brasileiros com precisão aceitável (≥ 85% de acurácia nos campos principais).

## Escopo

### ✅ O que está dentro

- Receber imagens via webhook do Telegram (FastAPI)
- Enviar imagem para Claude Sonnet 4.6 (visão) via OpenRouter
- Extrair campos: valor, data, estabelecimento, descrição, CNPJ (se visível)
- Retornar JSON estruturado ao chat do Telegram
- Testar com pelo menos 20 comprovantes reais (PIX, cartão, boleto, NF)
- Cloudflare Tunnel para expor o webhook em dev local

### ❌ O que está fora

- Agente Categorizador
- Persistência em banco de dados
- Fluxo de confirmação interativo (inline keyboards)
- Relatórios
- Deploy em produção
- Suporte a PDF

## Stack da POC

| Componente | Tecnologia |
|---|---|
| Bot framework | python-telegram-bot |
| API server | FastAPI (webhook endpoint) |
| LLM Gateway | OpenRouter API |
| Modelo de visão | Claude Sonnet 4.6 (anthropic/claude-sonnet-4.6) |
| Túnel | Cloudflare Tunnel (cloudflared) |
| Linguagem | Python 3.12+ |

## Critérios de Sucesso

- [ ] Webhook recebe imagens e texto do Telegram sem erros
- [ ] Extração de **valor** correto em ≥ 90% dos comprovantes testados
- [ ] Extração de **data** correta em ≥ 85% dos comprovantes testados
- [ ] Extração de **estabelecimento** correto em ≥ 80% dos comprovantes testados
- [ ] Tempo de resposta < 10 segundos (do envio à resposta no chat)
- [ ] Custo por extração < $0.01 USD

## Prazo Estimado

**2 semanas** (10 dias úteis)

| Dia | Atividade |
|---|---|
| 1-2 | Setup do projeto, Telegram Bot + FastAPI + Cloudflare Tunnel |
| 3-5 | Integração OpenRouter + prompt engineering para extração |
| 6-7 | Testes com comprovantes reais, ajuste de prompts |
| 8-9 | Refino, tratamento de edge cases, métricas de acurácia |
| 10 | Documentação de resultados e decisão go/no-go |
