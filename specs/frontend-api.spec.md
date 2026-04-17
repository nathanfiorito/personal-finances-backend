# Spec: Frontend API

## Objetivo
Expor uma API REST para o frontend consumir dados do Personal Finances. Todas as rotas são protegidas por autenticação via Supabase Auth (JWT). O frontend envia o token JWT no header `Authorization: Bearer <token>`, e o backend valida o token antes de processar qualquer request.

## Entradas / Saídas

### Autenticação
- **Entrada:** Header `Authorization: Bearer <jwt>` em todas as rotas `/api/*`
- **Saída:** `401 Unauthorized` se ausente ou inválido; `403 Forbidden` se expirado

### Despesas
- **GET /api/expenses**
  - Entrada: query params opcionais `start` (YYYY-MM-DD), `end` (YYYY-MM-DD), `categoria_id` (int), `page` (int, default 1), `page_size` (int, default 20, max 100)
  - Saída: `{ items: Expense[], total: int, page: int, page_size: int }`

- **GET /api/expenses/{id}**
  - Entrada: `id` (UUID)
  - Saída: `Expense`

- **POST /api/expenses**
  - Entrada: body `{ valor, data, estabelecimento?, descricao?, categoria_id, cnpj?, tipo_entrada }`
  - Saída: `Expense` criada (201)

- **PUT /api/expenses/{id}**
  - Entrada: `id` (UUID) + body com campos a atualizar
  - Saída: `Expense` atualizada

- **DELETE /api/expenses/{id}**
  - Entrada: `id` (UUID)
  - Saída: `204 No Content`

### Categorias
- **GET /api/categories**
  - Saída: `{ id: int, nome: str, ativo: bool }[]`

- **POST /api/categories**
  - Entrada: body `{ nome: str }`
  - Saída: categoria criada (201)

- **PATCH /api/categories/{id}**
  - Entrada: `id` (int) + body `{ nome?: str, ativo?: bool }`
  - Saída: categoria atualizada

- **DELETE /api/categories/{id}**
  - Entrada: `id` (int)
  - Saída: `204 No Content` (desativa, não remove)

### Relatórios
- **GET /api/reports/summary**
  - Entrada: query params `start` (YYYY-MM-DD), `end` (YYYY-MM-DD) — ambos obrigatórios
  - Saída: `{ categoria: str, total: Decimal }[]` ordenado por total desc

- **GET /api/reports/monthly**
  - Entrada: query params opcionais `year` (int, default ano atual)
  - Saída: `{ month: int, total: Decimal, by_category: { categoria: str, total: Decimal }[] }[]`

### Exportação
- **GET /api/export/csv**
  - Entrada: query params `start` (YYYY-MM-DD), `end` (YYYY-MM-DD) — ambos obrigatórios
  - Saída: arquivo CSV com `Content-Disposition: attachment; filename=expenses_<start>_<end>.csv`

## Comportamentos

1. Toda rota `/api/*` exige JWT válido emitido pelo Supabase; validação via `client.auth.get_user(jwt)`.
2. `GET /api/expenses` filtra por período quando `start`/`end` fornecidos; sem filtro retorna todas com paginação.
3. `POST /api/expenses` persiste diretamente no banco sem passar pelo fluxo de extração por AI do bot.
4. `DELETE /api/categories/{id}` desativa a categoria (seta `ativo = false`) em vez de deletar o registro.
5. `GET /api/reports/monthly` retorna todos os meses do ano solicitado que tiverem ao menos uma despesa.
6. `GET /api/export/csv` retorna colunas: `id, data, estabelecimento, descricao, categoria, valor, cnpj, tipo_entrada, confianca, created_at`.
7. Paginação em `GET /api/expenses`: `page_size` máximo de 100; valores acima são truncados a 100.
8. `PATCH /api/categories/{id}` aceita atualização parcial (apenas `nome`, apenas `ativo`, ou ambos).

## Casos extremos / Erros

- JWT ausente ou malformado → `401 Unauthorized`
- JWT expirado → `403 Forbidden`
- `GET/PUT/DELETE /api/expenses/{id}` com UUID inexistente → `404 Not Found`
- `PATCH/DELETE /api/categories/{id}` com ID inexistente → `404 Not Found`
- `POST /api/categories` com nome duplicado → `409 Conflict`
- `POST /api/expenses` com `valor <= 0` ou `valor > 999999.99` → `422 Unprocessable Entity`
- `GET /api/reports/summary` ou `GET /api/export/csv` sem `start`/`end` → `422 Unprocessable Entity`
- `start` > `end` em qualquer filtro de período → `422 Unprocessable Entity`
- `page_size` > 100 → truncar para 100 (sem erro)

## Critérios de Aceite

- [ ] Request sem JWT retorna 401
- [ ] Request com JWT expirado retorna 403
- [ ] `GET /api/expenses` sem filtros retorna lista paginada de todas as despesas
- [ ] `GET /api/expenses?start=2025-01-01&end=2025-01-31` retorna apenas despesas do período
- [ ] `GET /api/expenses?categoria_id=1` filtra por categoria
- [ ] `POST /api/expenses` cria despesa e retorna 201 com o registro criado
- [ ] `PUT /api/expenses/{id}` atualiza e retorna despesa atualizada
- [ ] `DELETE /api/expenses/{id}` remove e retorna 204
- [ ] `GET /api/expenses/{id}` com UUID inexistente retorna 404
- [ ] `GET /api/categories` retorna apenas categorias com `ativo = true`
- [ ] `POST /api/categories` com nome duplicado retorna 409
- [ ] `DELETE /api/categories/{id}` desativa sem remover o registro
- [ ] `GET /api/reports/summary` retorna totais agrupados por categoria, ordenados por total desc
- [ ] `GET /api/reports/monthly` retorna breakdown mensal do ano solicitado
- [ ] `GET /api/export/csv` retorna arquivo CSV com header correto e dados do período
- [ ] `GET /api/export/csv` sem `start`/`end` retorna 422

### Invoice Import

- **POST /api/v1/invoices/import/preview**
  - Auth: `Authorization: Bearer <jwt>`
  - Entrada: `multipart/form-data`, campo `file` (PDF, ≤ 10 MB)
  - Saída: preview JSON (veja shape abaixo) — nenhum dado é persistido
  - Erros: `400` (não é PDF / tamanho excede 10 MB / PDF sem texto extraível), `422` (resposta do LLM inválida), `500` (falha de infra)

  ```json
  {
    "source_file_name": "Fatura_Itau_20260416.pdf",
    "detected_card": {
      "last_four_digits": "7981",
      "matched_card_id": 2,
      "matched_card_alias": "Itaú Uniclass Black",
      "matched_card_bank": "Itaú"
    },
    "items": [
      {
        "temp_id": "a1b2c3d4",
        "date": "2025-12-28",
        "establishment": "Google YouTube MemberSA",
        "description": null,
        "amount": 1.99,
        "transaction_type": "EXPENSE",
        "payment_method": "CREDIT",
        "suggested_category_id": 7,
        "suggested_category_name": "Serviços",
        "issuer_hint": "serviços",
        "is_international": false,
        "original_currency": null,
        "original_amount": null,
        "is_possible_duplicate": false,
        "duplicate_of_transaction_id": null,
        "confidence": 0.95
      }
    ]
  }
  ```

  `detected_card` semantics: se `last_four_digits` extraídos e coincidem com um cartão ativo → todos os campos populados. Se extraídos mas sem correspondência → `matched_card_id=null`, alias/bank null. Se não extraídos → `last_four_digits=null` e demais campos null. Nas duas últimas situações o frontend exibe um card picker obrigatório antes de habilitar o botão Importar.

- **POST /api/v1/invoices/import**
  - Auth: `Authorization: Bearer <jwt>`
  - Entrada: `application/json`

  ```json
  {
    "card_id": 2,
    "items": [
      {
        "date": "2025-12-28",
        "establishment": "Google YouTube MemberSA",
        "description": null,
        "amount": 1.99,
        "transaction_type": "EXPENSE",
        "payment_method": "CREDIT",
        "category_id": 7
      }
    ]
  }
  ```

  `card_id` de nível superior aplica-se a todos os itens do lote. `temp_id` não é enviado. `confidence` não é persistido (armazenado como `null`). Todas as linhas são inseridas em uma única transação de banco de dados com `entry_type='invoice'`.

  - Saída: `{ "imported_count": 52, "card_id": 2, "transaction_ids": ["uuid1", "uuid2", "..."] }`
  - Erros: `400` (validação: `card_id` ausente, data inválida, `amount` ≤ 0, `items` vazio), `422` (`card_id` ou qualquer `category_id` não encontrado/inativo — rollback completo do lote), `500` (falha de infra)

## Restrições técnicas

- Python 3.12+ / FastAPI
- Autenticação: Supabase Auth — validar JWT com `client.auth.get_user(jwt)` via `supabase-py`
- Banco: Supabase PostgreSQL via `supabase-py` (cliente async já existente em `src/services/database.py`)
- `categoria_id` nas despesas é FK para `categories.id` (INT)
- Rotas organizadas em `src/routers/` (um arquivo por domínio: `expenses.py`, `categories.py`, `reports.py`, `export.py`)
- Dependency injection do FastAPI para o guard de autenticação (`Depends(get_current_user)`)
- CORS já configurado em `src/main.py` para `*.nathanfiorito.com.br`
- Não usar o fluxo de agentes AI para criação manual de despesas via API
