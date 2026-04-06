# MVP-C2 — Exportação CSV/Excel (Pós-MVP)

**Fase:** Pós-MVP | **Estimativa:** 1 dia | **Prioridade:** Could-have

## Objetivo

Permitir exportar as despesas de um período como arquivo CSV ou Excel, enviado diretamente no Telegram.

## Uso

```
/exportar mes        → CSV do mês corrente
/exportar 2024-01    → CSV de janeiro de 2024
```

## Tarefas

- [ ] Handler `/exportar` com parsing de período
- [ ] `database.get_expenses_by_period()` → já existe (reutilizar)
- [ ] Gerar CSV em memória com `csv.DictWriter` (sem criar arquivo em disco):
  - Colunas: `data`, `valor`, `estabelecimento`, `categoria`, `descricao`, `cnpj`, `tipo_entrada`
- [ ] Enviar como `document` via Telegram com nome `despesas_{periodo}.csv`
- [ ] Dependência opcional `openpyxl` para versão Excel (`.xlsx`)

## Critérios de Aceite

- CSV aberto no Excel/Sheets sem erros de encoding (UTF-8 com BOM)
- Período sem despesas → mensagem "Nenhuma despesa no período"
- Arquivo gerado em memória, não salvo em disco

## Dependências

- MVP-M5 (persistência) — `get_expenses_by_period()`
