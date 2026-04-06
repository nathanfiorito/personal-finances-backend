import logging
from collections import Counter
from datetime import date
from decimal import Decimal

from src.config.settings import settings
from src.models.expense import Expense
from src.services import llm

logger = logging.getLogger(__name__)

_CATEGORY_EMOJI: dict[str, str] = {
    "Alimentação": "🍽️",
    "Transporte": "🚗",
    "Moradia": "🏠",
    "Saúde": "💊",
    "Educação": "📚",
    "Lazer": "🎬",
    "Vestuário": "👕",
    "Serviços": "🔧",
    "Pets": "🐾",
    "Outros": "📦",
}

_INSIGHT_PROMPT = """\
Você é um assistente financeiro pessoal. Analise os dados abaixo e gere um insight \
conciso e útil em português (máx. 2 frases). Seja direto, específico e prático.

Período: {start} a {end}
Total gasto: R$ {total}
Número de transações: {n_transacoes}

Por categoria:
{breakdown}

Top estabelecimentos: {top_estab}

Gere apenas o insight, sem introduções ou títulos.\
"""


def _fmt(v: Decimal) -> str:
    return f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


async def _generate_insight(
    start: date,
    end: date,
    total: Decimal,
    totals: dict[str, Decimal],
    expenses: list[Expense],
    top_estab: str,
) -> str:
    breakdown = "\n".join(
        f"  {cat}: R$ {_fmt(amt)} ({int(amt / total * 100)}%)"
        for cat, amt in sorted(totals.items(), key=lambda x: x[1], reverse=True)
    )
    prompt = _INSIGHT_PROMPT.format(
        start=start.strftime("%d/%m/%Y"),
        end=end.strftime("%d/%m/%Y"),
        total=_fmt(total),
        n_transacoes=len(expenses),
        breakdown=breakdown,
        top_estab=top_estab,
    )
    try:
        response = await llm.chat_completion(
            model=settings.model_vision,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
        )
        return response.strip()
    except Exception:
        logger.warning("Falha ao gerar insight de relatório")
        return "Não foi possível gerar o insight neste momento."


async def generate_report(start: date, end: date) -> str:
    from src.services import database

    expenses = await database.get_expenses_by_period(start, end)

    if not expenses:
        return (
            f"📊 Nenhuma despesa registrada entre "
            f"{start.strftime('%d/%m/%Y')} e {end.strftime('%d/%m/%Y')}."
        )

    # Aggregate locally — avoids a second DB round-trip
    totals: dict[str, Decimal] = {}
    for e in expenses:
        totals[e.categoria] = totals.get(e.categoria, Decimal("0")) + e.valor
    total = sum(totals.values(), Decimal("0"))

    # Category breakdown (sorted by amount desc)
    breakdown_lines = [
        f"  {_CATEGORY_EMOJI.get(cat, '📦')} {cat}: R$ {_fmt(amt)} ({int(amt / total * 100)}%)"
        for cat, amt in sorted(totals.items(), key=lambda x: x[1], reverse=True)
    ]

    # Top establishments
    counter = Counter(e.estabelecimento for e in expenses if e.estabelecimento)
    top_estab = ", ".join(f"{n} ({c}x)" for n, c in counter.most_common(3)) or "—"

    # Period label
    days = (end - start).days
    if days <= 7:
        periodo = f"Últimos 7 dias ({start.strftime('%d/%m')} – {end.strftime('%d/%m/%Y')})"
    else:
        periodo = f"{start.strftime('%d/%m')} – {end.strftime('%d/%m/%Y')}"

    insight = await _generate_insight(start, end, total, totals, expenses, top_estab)

    return "\n".join([
        f"📊 <b>Relatório — {periodo}</b>",
        "",
        f"💰 <b>Total: R$ {_fmt(total)}</b>",
        f"📋 Transações: {len(expenses)}",
        "",
        "<b>Por categoria:</b>",
        *breakdown_lines,
        "",
        f"💡 {insight}",
    ])
