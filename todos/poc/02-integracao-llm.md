# POC-02 — Integração OpenRouter + Prompt Engineering

**Fase:** POC | **Dias:** 3–5 | **Prioridade:** Must-have

## Objetivo

Integrar o Claude Sonnet 4.6 via OpenRouter para extração de dados estruturados de comprovantes de pagamento (imagens). Produzir JSON confiável com valor, data, estabelecimento e descrição.

## Tarefas

### Serviço LLM (`src/services/llm.py`)

- [ ] Criar cliente OpenRouter usando o SDK `openai` apontado para `https://openrouter.ai/api/v1`
- [ ] Configurar modelo padrão: `anthropic/claude-sonnet-4-6` (visão) e `anthropic/claude-haiku-4-5` (texto)
- [ ] Configurar timeout de 30s nas chamadas
- [ ] Implementar retry com backoff exponencial (3 tentativas)

### Agente Extrator (`src/agents/extractor.py`)

- [ ] Implementar `extract_from_image(image_bytes: bytes) -> ExtractedExpense`
  - Baixar imagem via Telegram File API
  - Encodar em base64
  - Enviar ao Sonnet 4.6 com o prompt de extração
  - Parsear resposta JSON com Pydantic
- [ ] Implementar `extract_from_text(text: str) -> ExtractedExpense`
  - Enviar ao Haiku 4.5 com prompt de extração simples
- [ ] Definir prompt de extração de imagem (ver seção Prompt abaixo)

### Modelo de Dados (`src/models/expense.py`)

- [ ] Criar `ExtractedExpense` (Pydantic model):
  ```python
  class ExtractedExpense(BaseModel):
      valor: Decimal
      data: date
      estabelecimento: str | None
      descricao: str | None
      cnpj: str | None
      tipo_entrada: Literal["imagem", "texto", "pdf"]
      confianca: float  # 0.0 a 1.0
      dados_raw: dict
  ```

### Handler de Mensagem (`src/handlers/message.py`)

- [ ] Handler para foto: baixa imagem e chama `extract_from_image`
- [ ] Handler para texto: chama `extract_from_text`
- [ ] Responder no Telegram com o JSON extraído formatado (para validação na POC)

## Prompt de Extração (Imagem)

```
Analise este comprovante de pagamento brasileiro e extraia as informações no formato JSON abaixo.
Retorne APENAS o JSON, sem texto adicional.

{
  "valor": <número decimal, ex: 45.90>,
  "data": "<ISO 8601, ex: 2024-01-15>",
  "estabelecimento": "<nome do estabelecimento ou null>",
  "descricao": "<descrição do pagamento ou null>",
  "cnpj": "<CNPJ formatado ou null>",
  "confianca": <0.0 a 1.0 — sua confiança na extração>
}

Regras:
- Para valor, use o valor TOTAL da transação
- Para data, use a data da transação (não a de emissão do comprovante)
- Se um campo não for legível, retorne null
- confianca deve refletir a qualidade geral da extração
```

## Critérios de Aceite

- Foto de comprovante retorna JSON válido no Telegram
- Texto livre ("gastei 50 no mercado") retorna JSON com valor e estabelecimento preenchidos
- Erros da API (timeout, resposta inválida) são tratados e reportados ao usuário com mensagem amigável
- JSON sempre validado pelo Pydantic antes de prosseguir

## Dependências

- POC-01 concluído (webhook funcionando)
