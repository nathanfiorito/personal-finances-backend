import logging
from datetime import date
from decimal import Decimal

from supabase import AsyncClient, acreate_client

from src.config.settings import settings
from src.models.expense import Expense, ExtractedExpense

logger = logging.getLogger(__name__)

_client: AsyncClient | None = None


async def _get_client() -> AsyncClient:
    global _client
    if _client is None:
        _client = await acreate_client(settings.supabase_url, settings.supabase_service_key)
    return _client


async def save_expense(expense: ExtractedExpense, categoria: str) -> str:
    client = await _get_client()
    record = {
        "valor": str(expense.valor),
        "data": expense.data.isoformat(),
        "estabelecimento": expense.estabelecimento,
        "descricao": expense.descricao,
        "categoria": categoria,
        "cnpj": expense.cnpj,
        "tipo_entrada": expense.tipo_entrada,
        "confianca": expense.confianca,
        "dados_raw": expense.dados_raw,
    }
    response = await client.table("expenses").insert(record).execute()
    return response.data[0]["id"]


async def get_recent_expenses(limit: int = 3) -> list[Expense]:
    client = await _get_client()
    response = (
        await client.table("expenses")
        .select("*")
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return [Expense(**row) for row in response.data]


async def get_expenses_by_period(start: date, end: date) -> list[Expense]:
    client = await _get_client()
    response = (
        await client.table("expenses")
        .select("*")
        .gte("data", start.isoformat())
        .lte("data", end.isoformat())
        .order("data")
        .execute()
    )
    return [Expense(**row) for row in response.data]


async def add_category(nome: str) -> None:
    client = await _get_client()
    await client.table("categories").insert({"nome": nome}).execute()


async def get_active_categories() -> list[str]:
    client = await _get_client()
    response = (
        await client.table("categories")
        .select("nome")
        .eq("ativo", True)
        .order("nome")
        .execute()
    )
    return [row["nome"] for row in response.data]


async def get_totals_by_category(start: date, end: date) -> dict[str, Decimal]:
    expenses = await get_expenses_by_period(start, end)
    totals: dict[str, Decimal] = {}
    for expense in expenses:
        totals[expense.categoria] = totals.get(expense.categoria, Decimal("0")) + expense.valor
    return totals
