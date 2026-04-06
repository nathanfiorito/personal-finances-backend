# MVP-M2 — Agente Extrator

**Fase:** MVP | **Estimativa:** 3 dias | **Prioridade:** Must-have

## Objetivo

Implementar o agente de extração de dados estruturados de comprovantes, evoluindo a versão da POC para produção: tratamento robusto de erros, fallbacks, validação de schema e suporte a texto livre além de imagens.

## Tarefas

### Serviço LLM (`src/services/llm.py`)

- [ X ] Criar `LLMClient` com:
  - Base URL: `https://openrouter.ai/api/v1`
  - Configuração de modelos via settings (não hardcoded)
  - Timeout de 30s
  - Retry com backoff exponencial: 3 tentativas, delays 1s / 2s / 4s
  - Log de custo estimado por chamada (tokens input/output)

### Agente Extrator (`src/agents/extractor.py`)

- [ X ] `extract_from_image(image_bytes: bytes) -> ExtractedExpense`
  - Modelo: `anthropic/claude-sonnet-4-6`
  - Encodar imagem em base64 e enviar como `image_url` no formato OpenAI Vision
  - Parsear resposta como JSON → validar com Pydantic
  - Se JSON inválido: tentar extrair JSON do texto (regex fallback)
  - Se falha após retries: raise `ExtractionError` com mensagem clara

- [ X ] `extract_from_text(text: str) -> ExtractedExpense`
  - Modelo: `anthropic/claude-haiku-4-5`
  - Prompt otimizado para texto livre informal (ex: "gastei 80 no posto")

- [ X ] Prompt de extração de imagem finalizado (com exemplos few-shot se necessário)
- [ X ] Prompt de extração de texto finalizado

### Modelo de Dados (`src/models/expense.py`)

- [ X ] `ExtractedExpense` (Pydantic):
  ```python
  class ExtractedExpense(BaseModel):
      valor: Decimal
      data: date
      estabelecimento: str | None = None
      descricao: str | None = None
      cnpj: str | None = None
      tipo_entrada: Literal["imagem", "texto", "pdf"]
      confianca: float = Field(ge=0.0, le=1.0)
      dados_raw: dict
  ```
- [ X ] Validador de CNPJ (formato XX.XXX.XXX/XXXX-XX)
- [ X ] Validador de valor (não negativo, máximo razoável)

### Tratamento de Erros

- [ X ] `ExtractionError` — falha na extração (LLM não retornou JSON válido)
- [ X ] `LLMTimeoutError` — timeout na chamada
- [ X ] `LLMRateLimitError` — rate limit da OpenRouter
- [ X ] Mensagens de erro amigáveis para o usuário no Telegram

### Testes

- [ X ] `tests/test_extractor.py`:
  - Mockar chamadas à OpenRouter
  - Testar extração de imagem com resposta JSON válida
  - Testar fallback para JSON inválido
  - Testar extração de texto com frases informais
  - Testar tratamento de timeout

## Critérios de Aceite

- Imagem de comprovante retorna `ExtractedExpense` válido
- Texto "gastei 120 no posto shell" retorna valor=120.00, estabelecimento="Posto Shell"
- Falhas de API reportadas ao usuário com mensagem amigável, não stacktrace

## Dependências

- MVP-M1 (webhook) concluído
- `OPENROUTER_API_KEY` configurada
- Resultados da POC-03 (prompts validados)
