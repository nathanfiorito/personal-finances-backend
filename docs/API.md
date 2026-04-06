# API Reference — FinBot

Documento de referência para o desenvolvimento do frontend. Cobre endpoints HTTP, modelos de dados, schema do banco e operações disponíveis.

---

## HTTP Endpoints

O backend expõe apenas 2 endpoints HTTP. A interface do usuário é inteiramente via Telegram Bot.

### `GET /health`

Health check da aplicação.

**Request:** sem parâmetros

**Response `200 OK`:**
```json
{ "status": "ok" }
```

---

### `POST /webhook`

Recebe atualizações do Telegram. Uso exclusivo pelo Telegram Bot API — não chamado diretamente pelo frontend.

**Headers obrigatórios:**
```
X-Telegram-Bot-Api-Secret-Token: <TELEGRAM_WEBHOOK_SECRET>
```

**Request body:** Telegram Update object (JSON)

**Response `200 OK`:**
```json
{ "ok": true }
```

**Response `403 Forbidden`:** token inválido ou chat_id não autorizado

**Rate limit:** 30 req/min por IP

---

## Acesso Direto ao Banco (Supabase)

O frontend pode acessar o Supabase diretamente via Supabase Client SDK ou REST API. Todas as tabelas têm RLS habilitado com service role.

**Variáveis de conexão:**
- `SUPABASE_URL` — URL do projeto Supabase
- `SUPABASE_SERVICE_KEY` — chave de service role (acesso total)

> **Nota:** Para o frontend web, use a **anon key** do Supabase (não a service key) e configure RLS adequadamente se o frontend precisar de acesso direto ao banco.

---

## Schema do Banco de Dados

### Tabela `expenses`

| Coluna | Tipo | Constraints | Descrição |
|---|---|---|---|
| `id` | `UUID` | PK, `DEFAULT gen_random_uuid()` | Identificador único |
| `valor` | `DECIMAL(10,2)` | `NOT NULL` | Valor da despesa |
| `data` | `DATE` | `NOT NULL` | Data da transação |
| `estabelecimento` | `VARCHAR(255)` | nullable | Nome do estabelecimento |
| `descricao` | `TEXT` | nullable | Descrição do que foi comprado/pago |
| `categoria_id` | `INT` | `NOT NULL`, FK → `categories(id)` | ID da categoria |
| `cnpj` | `VARCHAR(18)` | nullable | CNPJ no formato `XX.XXX.XXX/XXXX-XX` |
| `tipo_entrada` | `VARCHAR(20)` | `NOT NULL`, CHECK IN `('imagem','texto','pdf')` | Como a despesa foi registrada |
| `confianca` | `DECIMAL(3,2)` | CHECK `0.00–1.00` | Score de confiança da extração por IA |
| `dados_raw` | `JSONB` | `DEFAULT '{}'` | JSON bruto retornado pelo extrator |
| `created_at` | `TIMESTAMPTZ` | `DEFAULT NOW()` | Timestamp de criação |
| `updated_at` | `TIMESTAMPTZ` | `DEFAULT NOW()` | Timestamp de atualização |

**Indexes:** `data`, `categoria_id`, `(data, categoria_id)`

---

### Tabela `categories`

| Coluna | Tipo | Constraints | Descrição |
|---|---|---|---|
| `id` | `SERIAL` | PK | Identificador único |
| `nome` | `VARCHAR(100)` | `UNIQUE NOT NULL` | Nome da categoria |
| `ativo` | `BOOLEAN` | `DEFAULT TRUE` | Se a categoria está ativa |
| `created_at` | `TIMESTAMPTZ` | `DEFAULT NOW()` | Timestamp de criação |

**Categorias padrão (seed):**
`Alimentação`, `Educação`, `Lazer`, `Moradia`, `Outros`, `Pets`, `Saúde`, `Serviços`, `Transporte`, `Vestuário`

---

## Query de Despesas com Categoria (JOIN)

Para obter despesas com o nome da categoria, use o join implícito do Supabase:

```sql
SELECT
    e.id,
    e.valor,
    e.data,
    e.estabelecimento,
    e.descricao,
    c.nome AS categoria,
    e.categoria_id,
    e.cnpj,
    e.tipo_entrada,
    e.confianca,
    e.created_at
FROM expenses e
JOIN categories c ON e.categoria_id = c.id
WHERE e.data >= :start AND e.data <= :end
ORDER BY e.data ASC;
```

Via SDK Supabase:
```python
client.table("expenses").select("*, categories(nome)").gte("data", start).lte("data", end).order("data").execute()
```

---

## Modelos de Dados (Pydantic)

### `ExtractedExpense` — dados extraídos pelo LLM (pré-save)

```python
class ExtractedExpense(BaseModel):
    valor: Decimal          # positivo, max 999999.99
    data: date
    estabelecimento: str | None = None
    descricao: str | None = None
    cnpj: str | None = None  # auto-formatado: "XX.XXX.XXX/XXXX-XX"
    tipo_entrada: Literal["imagem", "texto", "pdf"]
    confianca: float = 0.5   # 0.0 a 1.0
    dados_raw: dict = {}
```

### `Expense` — despesa persistida no banco

```python
class Expense(BaseModel):
    id: UUID
    valor: Decimal
    data: date
    estabelecimento: str | None
    descricao: str | None
    categoria: str           # nome da categoria (via join)
    categoria_id: int | None
    cnpj: str | None
    tipo_entrada: str
    confianca: float | None
    created_at: datetime
```

---

## Operações do Banco (`services/database.py`)

### `save_expense(expense, categoria) -> str`

Salva uma despesa confirmada. Resolve o `categoria_id` a partir do nome.

**Campos inseridos em `expenses`:**
```python
{
    "valor": str(expense.valor),
    "data": expense.data.isoformat(),
    "estabelecimento": expense.estabelecimento,
    "descricao": expense.descricao,
    "categoria_id": <id da categoria>,
    "cnpj": expense.cnpj,
    "tipo_entrada": expense.tipo_entrada,
    "confianca": float(expense.confianca),
    "dados_raw": expense.dados_raw
}
```

**Retorna:** UUID da despesa criada (string)

---

### `get_expenses_by_period(start: date, end: date) -> list[Expense]`

Busca despesas em um intervalo de datas. Inclui join com `categories`.

**Query:** `data >= start AND data <= end`, ordenado por `data ASC`

---

### `get_recent_expenses(limit: int = 3) -> list[Expense]`

Retorna as N despesas mais recentes, ordenadas por `created_at DESC`. Usado pelo Duplicate Checker.

---

### `get_totals_by_category(start: date, end: date) -> dict[str, Decimal]`

Retorna o total gasto por categoria no período. Calculado em Python a partir de `get_expenses_by_period`.

**Retorno:**
```python
{
    "Alimentação": Decimal("245.90"),
    "Transporte": Decimal("123.50"),
    ...
}
```

---

### `get_active_categories() -> list[str]`

Retorna nomes de todas as categorias com `ativo = true`, ordenadas por nome.

---

### `add_category(nome: str) -> None`

Insere uma nova categoria na tabela `categories`.

---

## Comandos do Bot (Referência Completa)

| Comando | Parâmetros | Comportamento | Período padrão |
|---|---|---|---|
| `/start` | — | Mensagem de boas-vindas | — |
| `/ajuda` | — | Lista todos os comandos | — |
| `/relatorio` | `[periodo]` | Gera relatório HTML com breakdown por categoria + insight de IA | mês corrente |
| `/exportar` | `[periodo]` | Envia arquivo CSV com despesas do período | mês corrente |
| `/categorias` | — | Lista categorias ativas do banco | — |
| `/categorias add <nome>` | `<nome>` | Adiciona nova categoria, invalida cache | — |

**Formatos de período aceitos:**
| Token | Intervalo |
|---|---|
| *(vazio)* ou `mes` | 1º dia do mês corrente até hoje |
| `semana` | últimos 7 dias |
| `anterior` | mês anterior completo |
| `MM/AAAA` | mês específico (ex: `03/2025`) |

---

## Callbacks de Inline Keyboard

| `callback_data` | Ação |
|---|---|
| `confirm` | Inicia verificação de duplicatas, depois salva |
| `force_confirm` | Salva sem verificação de duplicatas |
| `cancel` | Descarta a despesa pendente |
| `edit_category` | Exibe teclado de seleção de categoria |
| `set_category:<nome>` | Atualiza categoria da despesa pendente e volta para confirmação |

---

## Relatório — Estrutura de Saída

O comando `/relatorio` retorna HTML formatado (parse_mode HTML do Telegram) com:

```
📊 Relatório — <período>

💰 Total: R$ 1.234,56
📦 <N> transações

Por categoria:
🍽️ Alimentação: R$ 456,78 (37%)
🚗 Transporte: R$ 234,56 (19%)
...

🏪 Top estabelecimentos:
• Mercado Extra (5x)
• Shell (3x)
• iFood (2x)

💡 <insight gerado pelo Sonnet 4.6>
```

**Emojis por categoria:**
| Categoria | Emoji |
|---|---|
| Alimentação | 🍽️ |
| Transporte | 🚗 |
| Moradia | 🏠 |
| Saúde | 💊 |
| Educação | 📚 |
| Lazer | 🎮 |
| Vestuário | 👕 |
| Serviços | 🔧 |
| Pets | 🐾 |
| Outros | 📦 |

---

## CSV — Estrutura de Saída

O comando `/exportar` gera um CSV com UTF-8 BOM (compatível com Excel).

**Campos (cabeçalho):**
```
data,valor,estabelecimento,categoria,descricao,cnpj,tipo_entrada
```

**Exemplo de linha:**
```
2025-03-15,45.90,Supermercado Extra,Alimentação,Compras do mês,,imagem
```

**Nome do arquivo:** `despesas_YYYY-MM-DD_YYYY-MM-DD.csv`

---

## Variáveis de Ambiente

| Variável | Obrigatório | Padrão | Descrição |
|---|---|---|---|
| `TELEGRAM_BOT_TOKEN` | Sim | — | Token do bot (@BotFather) |
| `TELEGRAM_WEBHOOK_SECRET` | Sim | — | Secret para validar webhook |
| `TELEGRAM_ALLOWED_CHAT_ID` | Sim | — | chat_id do usuário autorizado |
| `OPENROUTER_API_KEY` | Sim | — | API key do OpenRouter |
| `OPENROUTER_BASE_URL` | Não | `https://openrouter.ai/api/v1` | Base URL do OpenRouter |
| `MODEL_VISION` | Não | `anthropic/claude-sonnet-4-6` | Modelo para visão e relatórios |
| `MODEL_FAST` | Não | `anthropic/claude-haiku-4-5` | Modelo para texto e categorização |
| `SUPABASE_URL` | Sim | — | URL do projeto Supabase |
| `SUPABASE_SERVICE_KEY` | Sim | — | Chave service role do Supabase |

---

## Agentes de IA — Resumo

| Agente | Arquivo | Modelo | max_tokens | Entrada | Saída |
|---|---|---|---|---|---|
| Extrator (imagem) | `agents/extractor.py` | Sonnet 4.6 | 512 | Imagem base64 | JSON: valor, data, estabelecimento, cnpj, confiança |
| Extrator (texto) | `agents/extractor.py` | Haiku 4.5 | 256 | Texto livre | JSON: valor, data, estabelecimento, descrição, confiança |
| Extrator (PDF) | `agents/extractor.py` | Haiku 4.5 ou Sonnet 4.6 | 256/512 | PDF (texto extraído ou imagem) | JSON: mesmos campos |
| Categorizador | `agents/categorizer.py` | Haiku 4.5 | 20 | ExtractedExpense | Nome da categoria |
| Verificador duplicatas | `agents/duplicate_checker.py` | Haiku 4.5 | 80 | Nova despesa + 3 recentes | `"OK"` ou `"DUPLICATA: <motivo>"` |
| Gerador de relatório | `agents/reporter.py` | Sonnet 4.6 | 200 | Totais por categoria, top estabelecimentos | Texto em português (2 frases) |

---

## Estado Temporário (Pending Store)

Entre a extração e a confirmação do usuário, a despesa fica armazenada em memória:

```python
# src/models/pending.py
_store: dict[int, _PendingExpense]  # keyed by chat_id

class _PendingExpense:
    extracted: ExtractedExpense
    categoria: str
    message_id: int      # ID da mensagem de confirmação no Telegram
    created_at: datetime
    # TTL: 10 minutos
```

- Uma despesa pendente por `chat_id` por vez
- Expirada automaticamente após 10 minutos
- Deletada ao confirmar, cancelar, ou timeout
