import contextlib
import logging
import time
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


@contextlib.asynccontextmanager
async def _timed_db(operation: str):
    """Context manager that logs the duration of a Supabase query."""
    t = time.perf_counter()
    try:
        yield
    finally:
        logger.info("DB %-45s %.0fms", operation, (time.perf_counter() - t) * 1000)


async def _get_category_id(client: AsyncClient, nome: str) -> int | None:
    async with _timed_db("categories.select(id).eq(nome)"):
        response = await client.table("categories").select("id").eq("nome", nome).limit(1).execute()
    if response.data:
        return response.data[0]["id"]
    return None


def _parse_expense_row(row: dict) -> Expense:
    row = dict(row)
    categories_data = row.pop("categories", None)
    if categories_data:
        row["categoria"] = categories_data["nome"]
    return Expense(**row)


async def save_expense(expense: ExtractedExpense, categoria: str) -> str:
    client = await _get_client()
    categoria_id = await _get_category_id(client, categoria)
    record = {
        "valor": str(expense.valor),
        "data": expense.data.isoformat(),
        "estabelecimento": expense.estabelecimento,
        "descricao": expense.descricao,
        "categoria_id": categoria_id,
        "cnpj": expense.cnpj,
        "tipo_entrada": expense.tipo_entrada,
        "transaction_type": expense.transaction_type,
        "confianca": expense.confianca,
        "dados_raw": expense.dados_raw,
    }
    async with _timed_db("transactions.insert"):
        response = await client.table("transactions").insert(record).execute()
    return response.data[0]["id"]


async def get_recent_expenses(limit: int = 3) -> list[Expense]:
    client = await _get_client()
    async with _timed_db(f"transactions.select(*).order(created_at).limit({limit})"):
        response = (
            await client.table("transactions")
            .select("*, categories(nome)")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
    return [_parse_expense_row(row) for row in response.data]


async def get_expenses_by_period(
    start: date,
    end: date,
    transaction_type: str | None = None,
) -> list[Expense]:
    client = await _get_client()
    async with _timed_db(f"transactions.select(*).period({start},{end})"):
        query = (
            client.table("transactions")
            .select("*, categories(nome)")
            .gte("data", start.isoformat())
            .lte("data", end.isoformat())
        )
        if transaction_type is not None:
            query = query.eq("transaction_type", transaction_type)
        response = await query.order("data").execute()
    return [_parse_expense_row(row) for row in response.data]


async def add_category(nome: str) -> None:
    client = await _get_client()
    async with _timed_db("categories.insert"):
        await client.table("categories").insert({"nome": nome}).execute()


async def get_active_categories() -> list[str]:
    client = await _get_client()
    async with _timed_db("categories.select(nome).eq(ativo=True)"):
        response = (
            await client.table("categories")
            .select("nome")
            .eq("ativo", True)
            .order("nome")
            .execute()
        )
    return [row["nome"] for row in response.data]


async def get_totals_by_category(
    start: date,
    end: date,
    transaction_type: str | None = None,
) -> dict[str, Decimal]:
    expenses = await get_expenses_by_period(start, end, transaction_type)
    totals: dict[str, Decimal] = {}
    for expense in expenses:
        totals[expense.categoria] = totals.get(expense.categoria, Decimal("0")) + expense.valor
    return totals


async def get_expenses_paginated(
    start: date | None,
    end: date | None,
    categoria_id: int | None,
    page: int,
    page_size: int,
    transaction_type: str | None = None,
) -> tuple[list[Expense], int]:
    client = await _get_client()
    query = client.table("transactions").select("*, categories(nome)", count="exact")
    if start:
        query = query.gte("data", start.isoformat())
    if end:
        query = query.lte("data", end.isoformat())
    if categoria_id is not None:
        query = query.eq("categoria_id", categoria_id)
    if transaction_type is not None:
        query = query.eq("transaction_type", transaction_type)
    offset = (page - 1) * page_size
    query = query.order("data", desc=True).range(offset, offset + page_size - 1)
    async with _timed_db(f"transactions.select(*).paginated(page={page},size={page_size})"):
        response = await query.execute()
    total = response.count or 0
    return [_parse_expense_row(row) for row in response.data], total


async def get_expense_by_id(expense_id: str) -> Expense | None:
    client = await _get_client()
    async with _timed_db(f"transactions.select(*).eq(id={expense_id[:8]}…)"):
        response = (
            await client.table("transactions")
            .select("*, categories(nome)")
            .eq("id", expense_id)
            .limit(1)
            .execute()
        )
    if not response.data:
        return None
    return _parse_expense_row(response.data[0])


async def create_expense_direct(record: dict) -> Expense:
    client = await _get_client()
    async with _timed_db("transactions.insert.select(*)"):
        response = (
            await client.table("transactions")
            .insert(record)
            .select("*, categories(nome)")
            .execute()
        )
    return _parse_expense_row(response.data[0])


async def update_expense(expense_id: str, data: dict) -> Expense | None:
    client = await _get_client()
    async with _timed_db(f"transactions.update.eq(id={expense_id[:8]}…)"):
        response = (
            await client.table("transactions")
            .update(data)
            .eq("id", expense_id)
            .select("*, categories(nome)")
            .execute()
        )
    if not response.data:
        return None
    return _parse_expense_row(response.data[0])


async def delete_expense(expense_id: str) -> bool:
    client = await _get_client()
    async with _timed_db(f"transactions.delete.eq(id={expense_id[:8]}…)"):
        response = (
            await client.table("transactions")
            .delete()
            .eq("id", expense_id)
            .select("id")
            .execute()
        )
    return bool(response.data)


async def get_all_categories() -> list[dict]:
    client = await _get_client()
    async with _timed_db("categories.select(id,nome,ativo).eq(ativo=True)"):
        response = (
            await client.table("categories")
            .select("id, nome, ativo")
            .eq("ativo", True)
            .order("nome")
            .execute()
        )
    return response.data


async def create_category_full(nome: str) -> dict:
    client = await _get_client()
    async with _timed_db("categories.insert.select(*)"):
        response = (
            await client.table("categories")
            .insert({"nome": nome})
            .select("id, nome, ativo")
            .execute()
        )
    return response.data[0]


async def update_category(category_id: int, data: dict) -> dict | None:
    client = await _get_client()
    async with _timed_db(f"categories.update.eq(id={category_id})"):
        response = (
            await client.table("categories")
            .update(data)
            .eq("id", category_id)
            .select("id, nome, ativo")
            .execute()
        )
    if not response.data:
        return None
    return response.data[0]


async def deactivate_category(category_id: int) -> bool:
    client = await _get_client()
    async with _timed_db(f"categories.update(ativo=False).eq(id={category_id})"):
        response = (
            await client.table("categories")
            .update({"ativo": False})
            .eq("id", category_id)
            .select("id")
            .execute()
        )
    return bool(response.data)


async def get_expenses_by_year(
    year: int,
    transaction_type: str | None = None,
) -> list[Expense]:
    return await get_expenses_by_period(date(year, 1, 1), date(year, 12, 31), transaction_type)
