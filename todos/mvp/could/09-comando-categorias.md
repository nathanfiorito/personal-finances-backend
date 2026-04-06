# MVP-C1 — Comando /categorias (Pós-MVP)

**Fase:** Pós-MVP | **Estimativa:** 2 dias | **Prioridade:** Could-have

## Objetivo

Permitir ao usuário listar as categorias existentes e futuramente criar/editar categorias personalizadas.

## Uso

```
/categorias          → lista categorias ativas
/categorias add      → inicia fluxo de criação (Pós-MVP)
```

## Tarefas

### Schema (Supabase)

- [ ] Criar tabela `categories` (ver `ARCHITECTURE.md`):
  ```sql
  CREATE TABLE categories (
      id SERIAL PRIMARY KEY,
      nome VARCHAR(100) UNIQUE NOT NULL,
      descricao TEXT,
      keywords TEXT[],
      ativo BOOLEAN DEFAULT TRUE,
      created_at TIMESTAMPTZ DEFAULT NOW()
  );
  ```
- [ ] Popular com as 10 categorias padrão

### Database (`src/services/database.py`)

- [ ] `get_active_categories() -> list[str]`

### Handler (`src/handlers/commands.py`)

- [ ] `/categorias` → listar categorias ativas formatadas

### Integração com Categorizador

- [ ] `categorizer.py` deve buscar categorias do banco ao invés de lista hardcoded
- [ ] Cachear categorias por 5 minutos para evitar query a cada categorização

## Dependências

- MVP-M5 (persistência) — precisa da tabela `categories` no Supabase
