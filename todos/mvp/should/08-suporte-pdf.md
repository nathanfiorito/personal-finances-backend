# MVP-S3 — Suporte a PDF de NF-e

**Fase:** MVP | **Estimativa:** 2 dias | **Prioridade:** Should-have

## Objetivo

Permitir que o usuário envie PDFs de Nota Fiscal Eletrônica (NF-e) e extraia os dados automaticamente, assim como já funciona para imagens e texto.

## Contexto

NF-e em PDF geralmente contém texto extraível (não é scan). A estratégia é:
1. Extrair texto do PDF com `pdfplumber` ou `pymupdf`
2. Enviar o texto ao Haiku 4.5 para extração estruturada (mais barato que Sonnet para texto)
3. Se texto não extraível (PDF de imagem escaneada): fazer fallback para Sonnet 4.6 com visão (converter primeira página em imagem)

## Tarefas

### Extração de Texto do PDF

- [ ] Adicionar dependência: `pdfplumber` (ou `pymupdf`)
- [ ] Criar `extract_text_from_pdf(pdf_bytes: bytes) -> str | None`
  - Extrair texto de todas as páginas
  - Retornar `None` se PDF não contiver texto legível (< 50 chars)

### Fallback para Visão (PDF escaneado)

- [ ] Se `extract_text_from_pdf` retornar `None`:
  - Converter primeira página do PDF em imagem (`pdf2image` ou `pymupdf`)
  - Enviar ao `extract_from_image()` do Agente Extrator

### Agente Extrator (`src/agents/extractor.py`)

- [ ] `extract_from_pdf(pdf_bytes: bytes) -> ExtractedExpense`
  1. Tentar extração de texto
  2. Se texto disponível → `extract_from_text(text)` com tipo `"pdf"`
  3. Se não → converter para imagem → `extract_from_image(image_bytes)` com tipo `"pdf"`

### Handler (`src/handlers/message.py`)

- [ ] Detectar PDF pelo `mime_type == "application/pdf"` no `message.document`
- [ ] Baixar arquivo e chamar `extract_from_pdf()`
- [ ] Continuar fluxo normal (categorização → confirmação → persistência)

### Dependências Python

- [ ] Adicionar ao `requirements.txt`:
  - `pdfplumber`
  - `pdf2image` (requer `poppler` instalado no sistema)
  - Alternativa sem binário externo: `pymupdf` (inclui tudo)

### Testes

- [ ] `tests/test_extractor.py`: testar PDF com texto extraível
- [ ] Testar fallback para PDF escaneado (mockar conversão para imagem)

## Critérios de Aceite

- NF-e em PDF com texto extraível → extração via Haiku (custo menor)
- PDF escaneado → fallback automático para Sonnet com visão
- Arquivo muito grande (> 10MB) → mensagem de erro amigável ao usuário
- `tipo_entrada` salvo como `"pdf"` no banco

## Dependências

- MVP-M2 (agente extrator) — estende `extract_from_text` e `extract_from_image`
- MVP-M1 (webhook) — detecção de PDF no handler de mensagens
