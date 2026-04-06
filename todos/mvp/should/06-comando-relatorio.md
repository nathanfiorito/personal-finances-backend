# MVP-S1 — Comando /relatorio

**Fase:** MVP | **Estimativa:** 3 dias | **Prioridade:** Should-have

## Objetivo

Implementar o comando `/relatorio` que gera um resumo financeiro por período (semana ou mês), com breakdown por categoria e insight gerado pelo Sonnet 4.6.

## Uso

```
/relatorio semana   → últimos 7 dias
/relatorio mes      → mês corrente (1º ao dia atual)
/relatorio          → padrão: mês corrente
```

## Tarefas

### Handler de Comando (`src/handlers/commands.py`)

- [ X ] Parsear argumento do comando (`semana` ou `mes`)
- [ X ] Calcular período:
  - `semana`: `today - 7 dias` até `today`
  - `mes`: `primeiro dia do mês corrente` até `today`
- [ X ] Enviar "Gerando relatório..." enquanto processa
- [ X ] Chamar `reporter.generate_report(start, end)`
- [ X ] Enviar resposta formatada

### Agente de Relatório (`src/agents/reporter.py`)

- [ X ] `generate_report(start: date, end: date) -> str`
  1. `database.get_totals_by_category(start, end)` → dict de totais
  2. `database.get_expenses_by_period(start, end)` → lista de despesas
  3. Calcular total geral
  4. Enviar ao Sonnet 4.6 com dados + prompt para gerar insight
  5. Retornar mensagem formatada

### Prompt de Relatório

```
Com base nas despesas abaixo, gere um resumo financeiro conciso em português.
Inclua: total gasto, breakdown por categoria e um insight sobre o padrão de gastos.
Seja direto e útil, como um assistente financeiro pessoal.

Período: {start} a {end}
Total: R$ {total}

Por categoria:
{categoria_breakdown}

Top estabelecimentos:
{top_estabelecimentos}
```

### Formatação da Mensagem

```
📊 Relatório — {período}

💰 Total: R$ {total}

Por categoria:
  🍽️ Alimentação: R$ 320,50 (35%)
  🚗 Transporte: R$ 180,00 (20%)
  🏠 Moradia: R$ 250,00 (27%)
  ...

💡 {insight gerado pelo Sonnet}
```

### Testes

- [ X ] Testar parsing de argumentos do comando
- [ X ] Testar cálculo de período para `semana` e `mes`
- [ X ] Testar formatação com dados de fixture (mockar DB e LLM)

## Critérios de Aceite

- `/relatorio semana` e `/relatorio mes` funcionam sem erro
- Relatório com 0 despesas retorna mensagem amigável ("Nenhuma despesa registrada neste período")
- Insight gerado pelo LLM é coerente com os dados
- Totais batem com soma das despesas individuais

## Dependências

- MVP-M5 (persistência) concluído — precisa de `get_totals_by_category` e `get_expenses_by_period`
