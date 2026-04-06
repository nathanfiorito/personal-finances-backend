# MVP-M5 — Persistência no Supabase

**Fase:** MVP | **Estimativa:** 2 dias | **Prioridade:** Must-have

## Objetivo

Implementar a camada de persistência no Supabase (PostgreSQL), incluindo criação do schema, operações CRUD e queries de relatório.

## Tarefas

### Schema do Banco (Supabase SQL Editor)

- [ ] Criar tabela `expenses`:
  ```sql
  CREATE TABLE expenses (
      id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
      valor DECIMAL(10,2) NOT NULL,
      data DATE NOT NULL,
      estabelecimento VARCHAR(255),
      descricao TEXT,
      categoria VARCHAR(100) NOT NULL,
      cnpj VARCHAR(18),
      localizacao VARCHAR(255),
      tipo_entrada VARCHAR(20) NOT NULL, -- 'imagem', 'texto', 'pdf'
      confianca DECIMAL(3,2),
      dados_raw JSONB,
      created_at TIMESTAMPTZ DEFAULT NOW(),
      updated_at TIMESTAMPTZ DEFAULT NOW()
  );
  ```
- [ ] Criar índices:
  ```sql
  CREATE INDEX idx_expenses_data ON expenses(data);
  CREATE INDEX idx_expenses_categoria ON expenses(categoria);
  CREATE INDEX idx_expenses_data_categoria ON expenses(data, categoria);
  ```
- [ ] Habilitar Row Level Security (RLS) na tabela
- [ ] Criar política RLS para service role (acesso total via `SUPABASE_SERVICE_KEY`)

### Serviço de Banco (`src/services/database.py`)

- [ ] `DatabaseClient` usando `supabase-py`:
  - Inicializar com `SUPABASE_URL` e `SUPABASE_SERVICE_KEY`
  
- [ ] `save_expense(expense: ExtractedExpense, categoria: str) -> str` (retorna UUID)
  - Inserir no Supabase via client
  - Usar queries parametrizadas (nunca string concatenation)
  
- [ ] `get_expenses_by_period(start: date, end: date) -> list[Expense]`
  - Para uso nos relatórios
  
- [ ] `get_totals_by_category(start: date, end: date) -> dict[str, Decimal]`
  - Agrega por categoria para relatórios

### Modelo de Dados Persistido (`src/models/expense.py`)

- [ ] `Expense` (Pydantic — representa registro salvo):
  ```python
  class Expense(BaseModel):
      id: UUID
      valor: Decimal
      data: date
      estabelecimento: str | None
      descricao: str | None
      categoria: str
      cnpj: str | None
      tipo_entrada: str
      confianca: float | None
      created_at: datetime
  ```

### Segurança

- [ ] Usar `SUPABASE_SERVICE_KEY` (não `ANON_KEY`) para operações server-side
- [ ] Garantir que nenhuma query usa f-strings ou concatenação com input do usuário

### Testes

- [ ] `tests/test_database.py`:
  - Testar `save_expense` com dados válidos (mockar Supabase client)
  - Testar `get_totals_by_category` com dados de fixture

## Critérios de Aceite

- `save_expense()` retorna UUID válido após inserção
- Dados persistidos são recuperáveis por período e categoria
- RLS habilitado na tabela `expenses`

## Variáveis de Ambiente

```env
SUPABASE_URL=
SUPABASE_SERVICE_KEY=
```

## Dependências

- MVP-M4 (fluxo de confirmação) — `save_expense` é chamado após confirmação
- Conta Supabase configurada com projeto criado
