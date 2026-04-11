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

_PROMPT_IMAGE = """Analyze this Brazilian payment receipt and extract the information in the JSON format below.
Return ONLY the JSON, no additional text, no markdown, no explanations.

{
  "amount": <positive decimal number, e.g.: 45.90>,
  "date": "<transaction date in ISO 8601, e.g.: 2024-01-15>",
  "establishment": "<establishment name or null>",
  "description": "<short payment description or null>",
  "tax_id": "<establishment CNPJ tax ID or null>",
  "transaction_type": "<\"income\" for money coming in (received, refund, salary, transfer received) or \"outcome\" for money going out (purchase, payment, bill). When in doubt, use \"outcome\">",
  "confidence": <number between 0.0 and 1.0 indicating your confidence in the extraction>
}

Rules:
- amount: use the TOTAL transaction value. Brazilian comma (45,90) becomes decimal point (45.90).
- date: use the transaction date, not the issue date. If ambiguous (mm/dd vs dd/mm), prefer Brazilian format (dd/mm).
- establishment: commercial name, not legal entity name.
- If a field is not legible or does not exist, use null.
- confidence should reflect the OVERALL quality of the extraction (1.0 = all fields clearly legible)."""

_PROMPT_TEXT = """Extract the financial information from the message below and return ONLY a JSON, no additional text.

{{
  "amount": <positive decimal number, e.g.: 45.90>,
  "date": "<date in ISO 8601 or null if not mentioned>",
  "establishment": "<place/establishment name or null>",
  "description": "<description of what was purchased/paid/received or null>",
  "tax_id": null,
  "transaction_type": "<\"income\" for money coming in (received, salary, refund, transfer received, sale) or \"outcome\" for money going out (bought, paid, spent, bill). When in doubt, use \"outcome\">",
  "confidence": <0.0 to 1.0>
}}

Rules:
- If the date is not mentioned, use null (do not invent a date).
- Values like "50 reais", "R$ 50", "50,00" or "50" should become 50.0.
- Abbreviations and typos are common — try to infer the establishment.
- confidence: the clearer the message, the higher.

Message: "{texto}" """


class ExtractionError(Exception):
    pass


def _parse_llm_json(raw: str) -> dict:
    """Extract JSON from the LLM response, with regex fallback if needed."""
    text = raw.strip()

    # Remove markdown blocks ```json ... ```
    text = re.sub(r"```(?:json)?\s*", "", text).strip("`").strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to extract the first JSON object from text
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass

    raise ExtractionError(f"Failed to parse JSON from response: {raw[:200]}")


def _build_expense(data: dict, entry_type: str) -> ExtractedExpense:
    """Build ExtractedExpense from the dict returned by the LLM."""
    # Normalize amount
    raw_amount = data.get("amount")
    if raw_amount is None:
        raise ExtractionError("Missing 'amount' field in LLM response")
    try:
        amount = Decimal(str(raw_amount))
    except InvalidOperation:
        raise ExtractionError(f"Invalid amount: {raw_amount!r}")

    # Normalize date
    raw_date = data.get("date")
    parsed_date: date | None = None
    if raw_date:
        try:
            parsed_date = date.fromisoformat(raw_date)
        except (ValueError, TypeError):
            logger.warning("Invalid date returned by LLM: %r -- using None", raw_date)

    raw_type = data.get("transaction_type", "outcome")
    transaction_type = raw_type if raw_type in ("income", "outcome") else "outcome"

    return ExtractedExpense(
        amount=amount,
        date=parsed_date or date.today(),
        establishment=data.get("establishment") or None,
        description=data.get("description") or None,
        tax_id=data.get("tax_id") or None,
        entry_type=entry_type,
        transaction_type=transaction_type,
        confidence=float(data.get("confidence", 0.5)),
        raw_data=data,
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
    expense = _build_expense(data, entry_type="imagem")
    logger.info(
        "Image extraction: amount=%.2f establishment=%r confidence=%.2f",
        expense.amount,
        expense.establishment,
        expense.confidence,
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
        logger.warning("pdfplumber failed to extract text from PDF")
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
        logger.info("PDF with extractable text — using Haiku")
        expense = await extract_from_text(text)
    else:
        logger.info("PDF without text — converting to image and using Sonnet")
        image_bytes = _pdf_to_image(pdf_bytes)
        expense = await extract_from_image(image_bytes)
    return expense.model_copy(update={"entry_type": "pdf"})


async def extract_from_text(text: str) -> ExtractedExpense:
    prompt = _PROMPT_TEXT.format(texto=text.replace('"', "'"))
    messages = [{"role": "user", "content": prompt}]

    raw = await llm.chat_completion(
        model=settings.model_fast,
        messages=messages,
        max_tokens=256,
    )

    data = _parse_llm_json(raw)
    expense = _build_expense(data, entry_type="texto")
    logger.info(
        "Text extraction: amount=%.2f establishment=%r confidence=%.2f",
        expense.amount,
        expense.establishment,
        expense.confidence,
    )
    return expense
