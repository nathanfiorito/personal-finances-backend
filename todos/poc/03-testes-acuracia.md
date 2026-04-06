# POC-03 — Testes de Acurácia com Comprovantes Reais

**Fase:** POC | **Dias:** 6–9 | **Prioridade:** Must-have

## Objetivo

Validar que o extrator atinge os critérios mínimos de acurácia com pelo menos 20 comprovantes reais de tipos variados. Identificar e corrigir edge cases.

## Conjunto de Testes

Coletar ao menos 20 comprovantes, cobrindo os tipos:

| Tipo | Qtd mínima |
|---|---|
| Comprovante PIX (app bancário) | 5 |
| Comprovante de cartão (crédito/débito) | 5 |
| Nota fiscal de restaurante/loja | 5 |
| Boleto bancário quitado | 3 |
| Comprovante de recarga / pedágio / etc. | 2 |

## Planilha de Avaliação

Para cada comprovante, registrar:

| # | Tipo | Valor esperado | Valor extraído | ✓? | Data esperada | Data extraída | ✓? | Estabelecimento esperado | Extraído | ✓? | Confiança |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | | | | | | | | | | | |

## Tarefas

- [ ] Montar dataset de 20+ comprovantes (fotos reais, anonimizadas se necessário)
- [ ] Criar script `tests/eval_extractor.py` para rodar todos os comprovantes e calcular métricas
- [ ] Executar avaliação e registrar resultados na planilha
- [ ] Analisar falhas:
  - Comprovantes com layout incomum
  - Valores com vírgula vs ponto
  - Datas ambíguas (dd/mm vs mm/dd)
  - Estabelecimentos com nomes técnicos/fiscais
- [ ] Ajustar prompt com base nas falhas identificadas
- [ ] Re-executar avaliação após ajuste de prompt
- [ ] Medir tempo de resposta médio por tipo de comprovante

## Critérios de Aceite (conforme POC.md)

| Campo | Meta |
|---|---|
| Valor | ≥ 90% correto |
| Data | ≥ 85% correto |
| Estabelecimento | ≥ 80% correto |
| Tempo de resposta | < 10 segundos |
| Custo por extração | < $0.01 USD |

## Dependências

- POC-02 concluído (extrator funcionando)
