# MVP-M4 — Fluxo de Confirmação (Inline Keyboards)

**Fase:** MVP | **Estimativa:** 2 dias | **Prioridade:** Must-have

## Objetivo

Apresentar ao usuário os dados extraídos + categoria antes de persistir, e aguardar confirmação explícita via inline keyboard do Telegram. Implementar estado temporário para manter a despesa pendente entre as interações.

## Fluxo

```
[Usuário envia foto]
    ↓
[Extração + Categorização]
    ↓
[Bot envia mensagem de confirmação com inline keyboard]

  Despesa detectada:
  💰 Valor: R$ 45,90
  📅 Data: 15/01/2024
  🏪 Estabelecimento: Supermercado Extra
  🏷️ Categoria: Alimentação

  [✅ Confirmar]  [✏️ Editar categoria]  [❌ Cancelar]

    ↓ (usuário clica Confirmar)
[Persistência no Supabase]
[Bot: "Despesa de R$ 45,90 em Alimentação registrada! ✅"]
```

## Tarefas

### Estado Temporário

- [ ] Criar `PendingExpense` para armazenar despesa aguardando confirmação:
  ```python
  class PendingExpense(BaseModel):
      extracted: ExtractedExpense
      categoria: str
      message_id: int  # para editar a mensagem original
      created_at: datetime
  ```
- [ ] Criar store in-memory simples: `dict[int, PendingExpense]` keyed por `chat_id`
- [ ] TTL de 10 minutos — expirar pendências antigas automaticamente

### Handler de Confirmação (`src/handlers/message.py`)

- [ ] Após extração + categorização, formatar e enviar mensagem de confirmação com `InlineKeyboardMarkup`:
  - Botão `✅ Confirmar` → callback `confirm:{chat_id}`
  - Botão `✏️ Editar categoria` → callback `edit_category:{chat_id}`
  - Botão `❌ Cancelar` → callback `cancel:{chat_id}`

### Handler de Callbacks (`src/handlers/callback.py`)

- [ ] `handle_confirm(chat_id)`:
  - Recuperar `PendingExpense` do store
  - Chamar `database.save_expense()`
  - Editar mensagem original com confirmação de sucesso
  - Remover do store

- [ ] `handle_cancel(chat_id)`:
  - Remover do store
  - Editar mensagem com "Despesa cancelada."

- [ ] `handle_edit_category(chat_id)`:
  - Enviar novo inline keyboard com as 10 categorias listadas
  - Callback de seleção: `set_category:{chat_id}:{categoria}`
  - Após seleção: atualizar `PendingExpense` e reapresentar tela de confirmação

### Testes

- [ ] Teste de confirmação: verificar que `save_expense` é chamado com dados corretos
- [ ] Teste de cancelamento: verificar que pending é removido e banco não é chamado
- [ ] Teste de edição de categoria: verificar que categoria é atualizada antes de salvar
- [ ] Teste de expiração: pendência com > 10 min deve ser ignorada

## Critérios de Aceite

- Dados apresentados de forma legível, com emoji e formatação clara
- Edição de categoria funciona e re-apresenta confirmação com nova categoria
- Despesa nunca é salva sem confirmação explícita
- Expiração de pendência retorna mensagem ao usuário ("Operação expirada, envie novamente")

## Dependências

- MVP-M2 (extrator) e MVP-M3 (categorizador) concluídos
- MVP-M5 (persistência) pode ser implementado em paralelo — interface `save_expense()` pode ser mockada inicialmente
