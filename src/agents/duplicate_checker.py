import logging

from src.config.settings import settings
from src.models.expense import Expense, ExtractedExpense
from src.services.llm import chat_completion

logger = logging.getLogger(__name__)

_PROMPT = """\
Analyze whether the new expense is a possible duplicate of any recent expenses.

New expense:
- Amount: R$ {amount}
- Date: {date}
- Establishment: {establishment}
- Description: {description}

Recent expenses:
{recent_lines}

Respond ONLY with one of the options:
- "DUPLICATE: <brief reason in Portuguese>" — if it is an obvious duplicate (same amount AND same place or description, with close date)
- "OK" — if not a duplicate

Be conservative: only mark as DUPLICATE if there is strong evidence. Similar expenses but with different amounts or places should be "OK".\
"""


async def check_duplicate(expense: ExtractedExpense, recent: list[Expense]) -> str | None:
    """Returns a reason string if a duplicate is detected, None otherwise.

    Failures are swallowed so a LLM outage never blocks saving an expense.
    """
    if not recent:
        return None

    recent_lines = [
        f"{i}. R$ {e.amount} | {e.date} | {e.establishment or '-'} | {e.description or '-'}"
        for i, e in enumerate(recent, 1)
    ]

    prompt = _PROMPT.format(
        amount=expense.amount,
        date=expense.date,
        establishment=expense.establishment or "not provided",
        description=expense.description or "not provided",
        recent_lines="\n".join(recent_lines),
    )

    try:
        response = await chat_completion(
            model=settings.model_fast,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=80,
        )
        response = response.strip()
        if response.upper().startswith("DUPLICATE:") or response.upper().startswith("DUPLICATA:"):
            prefix = "DUPLICATE:" if response.upper().startswith("DUPLICATE:") else "DUPLICATA:"
            return response[len(prefix):].strip()
        return None
    except Exception:
        logger.warning("AI duplicate check failed — proceeding without verification")
        return None
