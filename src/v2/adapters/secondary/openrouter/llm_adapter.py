import json
import logging
import re
from decimal import Decimal, InvalidOperation

from src.v2.domain.entities.expense import Expense, ExtractedExpense
from src.v2.domain.ports.llm_port import LLMPort
# Re-use the existing retry-aware chat_completion helper to avoid duplicating
# exponential back-off logic.
from src.services.llm import chat_completion

logger = logging.getLogger(__name__)


class OpenRouterLLMAdapter(LLMPort):
    """Implements LLMPort using OpenRouter (OpenAI-compatible API)."""

    def __init__(self, model_vision: str, model_fast: str) -> None:
        """
        Args:
            model_vision: Model ID for image extraction and reports
                          e.g. "anthropic/claude-sonnet-4-6"
            model_fast:   Model ID for text extraction, categorization,
                          and duplicate checking
                          e.g. "anthropic/claude-haiku-4-5"
        """
        self._model_vision = model_vision
        self._model_fast = model_fast

    # ── Extraction ────────────────────────────────────────────────────────────

    async def extract_from_image(self, image_b64: str) -> ExtractedExpense:
        prompt = _PROMPT_IMAGE
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"},
                    },
                ],
            }
        ]
        raw = await chat_completion(
            model=self._model_vision, messages=messages, max_tokens=500
        )
        return _parse_extracted(raw, entry_type="image")

    async def extract_from_text(self, text: str) -> ExtractedExpense:
        prompt = _PROMPT_TEXT.format(texto=text)
        messages = [{"role": "user", "content": prompt}]
        raw = await chat_completion(
            model=self._model_fast, messages=messages, max_tokens=300
        )
        return _parse_extracted(raw, entry_type="text")

    # ── Categorization ────────────────────────────────────────────────────────

    async def categorize(
        self, expense: ExtractedExpense, categories: list[str]
    ) -> str:
        prompt = _PROMPT_CATEGORIZE.format(
            categories=", ".join(categories),
            establishment=expense.establishment or "Não informado",
            description=expense.description or "Não informada",
        )
        raw = await chat_completion(
            model=self._model_fast,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=20,
        )
        category = raw.strip().rstrip(".")
        if category in categories:
            return category
        # Case-insensitive fallback
        for cat in categories:
            if cat.lower() == category.lower():
                return cat
        logger.warning("LLM returned unknown category %r — defaulting to Outros", category)
        return "Outros" if "Outros" in categories else categories[0]

    # ── Duplicate check ───────────────────────────────────────────────────────

    async def check_duplicate(
        self, expense: ExtractedExpense, recent: list[Expense]
    ) -> str | None:
        if not recent:
            return None
        recent_lines = "\n".join(
            f"- {e.date} | R${e.amount} | {e.establishment or 'N/A'} | {e.category}"
            for e in recent
        )
        new_line = (
            f"- {expense.date} | R${expense.amount} "
            f"| {expense.establishment or 'N/A'}"
        )
        prompt = _PROMPT_DUPLICATE.format(
            recent=recent_lines, new_expense=new_line
        )
        raw = await chat_completion(
            model=self._model_fast,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100,
        )
        raw = raw.strip()
        if raw.upper().startswith("DUPLICATA"):
            reason = raw[len("DUPLICATA"):].strip(" :-")
            return reason or "Despesa similar encontrada recentemente."
        return None

    # ── Report ────────────────────────────────────────────────────────────────

    async def generate_report(
        self, expenses: list[Expense], period: str
    ) -> str:
        totals: dict[str, Decimal] = {}
        for expense in expenses:
            totals[expense.category] = (
                totals.get(expense.category, Decimal("0")) + expense.amount
            )
        summary_lines = [
            f"- {cat}: R${total:.2f}" for cat, total in sorted(totals.items())
        ]
        prompt = _PROMPT_REPORT.format(
            period=period, summary="\n".join(summary_lines)
        )
        raw = await chat_completion(
            model=self._model_vision,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=120,
        )
        return raw.strip()


# ── Prompts ───────────────────────────────────────────────────────────────────

_PROMPT_IMAGE = """Analyze this Brazilian payment receipt and extract the information in the JSON format below.
Return ONLY the JSON, no additional text, no markdown, no explanations.

{
  "amount": <positive decimal number, e.g.: 45.90>,
  "date": "<transaction date in ISO 8601, e.g.: 2024-01-15>",
  "establishment": "<establishment name or null>",
  "description": "<short payment description or null>",
  "tax_id": "<establishment CNPJ tax ID or null>",
  "transaction_type": "<\"income\" for money coming in or \"outcome\" for money going out. When in doubt, use \"outcome\">",
  "confidence": <number between 0.0 and 1.0>
}

Rules:
- amount: use the TOTAL transaction value. Brazilian comma (45,90) becomes decimal point (45.90).
- date: use the transaction date, not the issue date. If ambiguous prefer Brazilian format (dd/mm).
- establishment: commercial name, not legal entity name.
- If a field is not legible or does not exist, use null."""

_PROMPT_TEXT = """Extract the financial information from the message below and return ONLY a JSON, no additional text.

{{
  "amount": <positive decimal number, e.g.: 45.90>,
  "date": "<date in ISO 8601 or null if not mentioned>",
  "establishment": "<place/establishment name or null>",
  "description": "<description of what was purchased/paid/received or null>",
  "tax_id": null,
  "transaction_type": "<\"income\" for money coming in or \"outcome\" for money going out. When in doubt, use \"outcome\">",
  "confidence": <0.0 to 1.0>
}}

Rules:
- If the date is not mentioned, use null (do not invent a date).
- Values like "50 reais", "R$ 50", "50,00" or "50" should become 50.0.
- confidence: the clearer the message, the higher.

Message: "{texto}" """

_PROMPT_CATEGORIZE = """Classifique a despesa abaixo em UMA das categorias: {categories}

Estabelecimento: {establishment}
Descrição: {description}

Responda APENAS com o nome exato da categoria, sem explicação."""

_PROMPT_DUPLICATE = """Compare the new expense with the recent expenses below.

Recent expenses:
{recent}

New expense:
{new_expense}

If the new expense appears to be a duplicate of one of the recent ones (same store, similar amount, same or consecutive days), respond with:
DUPLICATA: <brief reason in Portuguese>

If it is NOT a duplicate, respond with:
OK"""

_PROMPT_REPORT = """Você é um assistente financeiro pessoal. Analise o resumo de despesas abaixo e gere exatamente 2 frases de insight financeiro em português. Seja direto e útil.

Período: {period}
Despesas por categoria:
{summary}

Responda com exatamente 2 frases."""


# ── JSON parsing helpers ──────────────────────────────────────────────────────

def _parse_extracted(raw: str, entry_type: str) -> ExtractedExpense:
    data = _parse_llm_json(raw)
    try:
        amount = Decimal(str(data.get("amount", 0)))
    except InvalidOperation:
        amount = Decimal("0.01")

    from datetime import date as _date
    raw_date = data.get("date")
    parsed_date: _date | None = None
    if raw_date:
        try:
            from datetime import datetime
            parsed_date = datetime.fromisoformat(str(raw_date)).date()
        except (ValueError, TypeError):
            parsed_date = None

    return ExtractedExpense(
        amount=amount,
        date=parsed_date,
        establishment=data.get("establishment"),
        description=data.get("description"),
        tax_id=data.get("tax_id"),
        entry_type=entry_type,  # type: ignore[arg-type]
        transaction_type=data.get("transaction_type", "outcome"),  # type: ignore[arg-type]
        confidence=float(data.get("confidence", 0.5)),
    )


def _parse_llm_json(raw: str) -> dict:
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    logger.warning("Could not parse LLM JSON: %r", raw[:200])
    return {}
