# MVP-M3 — Agente Categorizador

**Fase:** MVP | **Estimativa:** 2 dias | **Prioridade:** Must-have

## Objetivo

Classificar automaticamente uma despesa extraída em uma das categorias pré-definidas usando Claude Haiku 4.5.

## Categorias Padrão

1. Alimentação
2. Transporte
3. Moradia
4. Saúde
5. Educação
6. Lazer
7. Vestuário
8. Serviços
9. Pets
10. Outros (fallback)

## Tarefas

### Agente Categorizador (`src/agents/categorizer.py`)

- [ X ] `categorize(expense: ExtractedExpense) -> str`
  - Modelo: `anthropic/claude-haiku-4-5`
  - Input: `estabelecimento`, `descricao`, `dados_raw` da despesa
  - Output: nome exato de uma das 10 categorias
  - Prompt deve listar as categorias com exemplos de cada uma
  - Se resposta inválida (categoria não reconhecida): retornar `"Outros"`
  - Não deve falhar — sempre retorna uma categoria válida

### Prompt de Categorização

```
Classifique a despesa abaixo em uma das categorias:
Alimentação, Transporte, Moradia, Saúde, Educação, Lazer, Vestuário, Serviços, Pets, Outros

Estabelecimento: {estabelecimento}
Descrição: {descricao}

Exemplos:
- "Restaurante Bom Sabor" → Alimentação
- "Shell" / "Posto Ipiranga" → Transporte
- "iFood" / "Rappi" → Alimentação
- "Drogasil" / "Farmácia" → Saúde

Responda APENAS com o nome exato da categoria, sem explicação.
```

### Testes

- [ X ] `tests/test_categorizer.py`:
  - Mockar chamada ao Haiku
  - Testar categorização de "Supermercado Extra" → Alimentação
  - Testar categorização de "Uber" → Transporte
  - Testar fallback quando LLM retorna categoria inválida

## Critérios de Aceite

- Sempre retorna uma das 10 categorias (nunca `None` ou categoria inválida)
- "iFood", "McDonald's", "Mercado" → Alimentação
- "Uber", "Shell", "Estacionamento" → Transporte
- Categorias desconhecidas → Outros

## Dependências

- MVP-M2 (extrator) concluído — recebe `ExtractedExpense` como input
