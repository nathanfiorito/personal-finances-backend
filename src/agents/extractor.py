import base64
import json
import logging
import re
from datetime import date
from decimal import Decimal, InvalidOperation

from src.config.settings import settings
from src.models.expense import ExtractedExpense
from src.services import llm

logger = logging.getLogger(__name__)

_PROMPT_IMAGE = """Analise este comprovante de pagamento brasileiro e extraia as informações no formato JSON abaixo.
Retorne APENAS o JSON, sem texto adicional, sem markdown, sem explicações.

{
  "valor": <número decimal positivo, ex: 45.90>,
  "data": "<data da transação em ISO 8601, ex: 2024-01-15>",
  "estabelecimento": "<nome do estabelecimento ou null>",
  "descricao": "<descrição resumida do pagamento ou null>",
  "cnpj": "<CNPJ do estabelecimento ou null>",
  "confianca": <número entre 0.0 e 1.0 indicando sua confiança na extração>
}

Regras:
- valor: use o valor TOTAL da transação. Vírgula brasileira (45,90) deve virar ponto decimal (45.90).
- data: use a data da transação, não a de emissão. Se ambígua (mm/dd vs dd/mm), prefira o formato brasileiro (dd/mm).
- estabelecimento: nome comercial, não razão social.
- Se um campo não for legível ou não existir, use null.
- confianca deve refletir a qualidade GERAL da extração (1.0 = todos os campos claramente legíveis)."""

_PROMPT_TEXT = """Extraia as informações de despesa da mensagem abaixo e retorne APENAS um JSON, sem texto adicional.

{{
  "valor": <número decimal positivo, ex: 45.90>,
  "data": "<data em ISO 8601 ou null se não mencionada>",
  "estabelecimento": "<nome do local/estabelecimento ou null>",
  "descricao": "<descrição do que foi comprado/pago ou null>",
  "cnpj": null,
  "confianca": <0.0 a 1.0>
}}

Regras:
- Se a data não for mencionada, use null (não invente uma data).
- Valores como "50 reais", "R$ 50", "50,00" ou "50" devem virar 50.0.
- Abreviações e erros de digitação são comuns — tente inferir o estabelecimento.
- confianca: quanto mais clara a mensagem, mais alto.

Mensagem: "{texto}" """


class ExtractionError(Exception):
    pass


def _parse_llm_json(raw: str) -> dict:
    """Extrai JSON da resposta do LLM, com fallback para regex se necessário."""
    text = raw.strip()

    # Remover blocos markdown ```json ... ```
    text = re.sub(r"```(?:json)?\s*", "", text).strip("`").strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Tentar extrair o primeiro objeto JSON do texto
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass

    raise ExtractionError(f"Não foi possível parsear JSON da resposta: {raw[:200]}")


def _build_expense(data: dict, tipo: str) -> ExtractedExpense:
    """Constrói ExtractedExpense a partir do dict retornado pelo LLM."""
    # Normalizar valor
    raw_valor = data.get("valor")
    if raw_valor is None:
        raise ExtractionError("Campo 'valor' ausente na resposta do LLM")
    try:
        valor = Decimal(str(raw_valor))
    except InvalidOperation:
        raise ExtractionError(f"Valor inválido: {raw_valor!r}")

    # Normalizar data
    raw_data = data.get("data")
    parsed_date: date | None = None
    if raw_data:
        try:
            parsed_date = date.fromisoformat(raw_data)
        except (ValueError, TypeError):
            logger.warning("Data inválida retornada pelo LLM: %r — usando None", raw_data)

    return ExtractedExpense(
        valor=valor,
        data=parsed_date or date.today(),
        estabelecimento=data.get("estabelecimento") or None,
        descricao=data.get("descricao") or None,
        cnpj=data.get("cnpj") or None,
        tipo_entrada=tipo,
        confianca=float(data.get("confianca", 0.5)),
        dados_raw=data,
    )


async def extract_from_image(image_bytes: bytes) -> ExtractedExpense:
    encoded = base64.standard_b64encode(image_bytes).decode()
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": _PROMPT_IMAGE},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{encoded}"},
                },
            ],
        }
    ]

    raw = await llm.chat_completion(
        model=settings.model_vision,
        messages=messages,
        max_tokens=512,
    )

    data = _parse_llm_json(raw)
    expense = _build_expense(data, tipo="imagem")
    logger.info(
        "Extração de imagem: valor=%.2f estabelecimento=%r confianca=%.2f",
        expense.valor,
        expense.estabelecimento,
        expense.confianca,
    )
    return expense


def _extract_text_from_pdf(pdf_bytes: bytes) -> str | None:
    """Extracts text from a PDF. Returns None if the PDF has no readable text (< 50 chars)."""
    try:
        import io
        import pdfplumber
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            text = "\n".join(page.extract_text() or "" for page in pdf.pages)
        text = text.strip()
        return text if len(text) >= 50 else None
    except Exception:
        logger.warning("pdfplumber falhou na extração de texto do PDF")
        return None


def _pdf_to_image(pdf_bytes: bytes) -> bytes:
    """Converts the first page of a PDF to a JPEG image using PyMuPDF."""
    import fitz  # pymupdf
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page = doc[0]
    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom for quality
    return pix.tobytes("jpeg")


async def extract_from_pdf(pdf_bytes: bytes) -> ExtractedExpense:
    text = _extract_text_from_pdf(pdf_bytes)
    if text:
        logger.info("PDF com texto extraível — usando Haiku")
        expense = await extract_from_text(text)
    else:
        logger.info("PDF sem texto — convertendo para imagem e usando Sonnet")
        image_bytes = _pdf_to_image(pdf_bytes)
        expense = await extract_from_image(image_bytes)
    return expense.model_copy(update={"tipo_entrada": "pdf"})


async def extract_from_text(text: str) -> ExtractedExpense:
    prompt = _PROMPT_TEXT.format(texto=text.replace('"', "'"))
    messages = [{"role": "user", "content": prompt}]

    raw = await llm.chat_completion(
        model=settings.model_fast,
        messages=messages,
        max_tokens=256,
    )

    data = _parse_llm_json(raw)
    expense = _build_expense(data, tipo="texto")
    logger.info(
        "Extração de texto: valor=%.2f estabelecimento=%r confianca=%.2f",
        expense.valor,
        expense.estabelecimento,
        expense.confianca,
    )
    return expense
