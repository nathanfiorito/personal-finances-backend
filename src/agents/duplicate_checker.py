import logging

from src.config.settings import settings
from src.models.expense import Expense, ExtractedExpense
from src.services.llm import chat_completion

logger = logging.getLogger(__name__)

_PROMPT = """\
Analise se a nova despesa é uma possível duplicata de alguma das despesas recentes.

Nova despesa:
- Valor: R$ {valor}
- Data: {data}
- Estabelecimento: {estabelecimento}
- Descrição: {descricao}

Despesas recentes:
{recentes}

Responda APENAS com uma das opções:
- "DUPLICATA: <motivo breve em português>" — se for duplicata óbvia (mesmo valor E mesmo local ou descrição, com data próxima)
- "OK" — se não for duplicata

Seja conservador: só marque como DUPLICATA se houver forte evidência. Despesas similares mas com valores ou locais diferentes devem ser "OK".\
"""


async def check_duplicate(expense: ExtractedExpense, recent: list[Expense]) -> str | None:
    """Returns a reason string if a duplicate is detected, None otherwise.

    Failures are swallowed so a LLM outage never blocks saving an expense.
    """
    if not recent:
        return None

    recentes_lines = [
        f"{i}. R$ {e.valor} | {e.data} | {e.estabelecimento or '-'} | {e.descricao or '-'}"
        for i, e in enumerate(recent, 1)
    ]

    prompt = _PROMPT.format(
        valor=expense.valor,
        data=expense.data,
        estabelecimento=expense.estabelecimento or "não informado",
        descricao=expense.descricao or "não informada",
        recentes="\n".join(recentes_lines),
    )

    try:
        response = await chat_completion(
            model=settings.model_fast,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=80,
        )
        response = response.strip()
        if response.upper().startswith("DUPLICATA:"):
            return response[len("DUPLICATA:"):].strip()
        return None
    except Exception:
        logger.warning("Falha na verificação de duplicidade via IA — prosseguindo sem verificar")
        return None
