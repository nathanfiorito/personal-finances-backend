import contextlib
import logging
import time
from datetime import date
from decimal import Decimal

from supabase import AsyncClient, acreate_client

from src.config.settings import settings
from src.models.expense import Expense, ExtractedExpense
from src.services import tracing

logger = logging.getLogger(__name__)

_client: AsyncClient | None = None


async def _get_client() -> AsyncClient:
    global _client
    if _client is None:
        _client = await acreate_client(settings.supabase_url, settings.supabase_service_key)
    return _client


def _db_span_attrs(operation: str) -> dict[str, str]:
    """Parse 'table.op(...)' into db.table and db.operation span attributes."""
    parts = operation.split(".", 1)
    table = parts[0]
    op = parts[1].split("(")[0].split(".")[0] if len(parts) > 1 else "query"
    return {"db.table": table, "db.operation": op}


@contextlib.asynccontextmanager
async def _timed_db(operation: str):
    """Context manager that logs and traces the duration of a Supabase query.

    Yields the span so callers can set extra attributes (e.g. db.rows).
    """
    t = time.perf_counter()
    with tracing.start_span(operation, _db_span_attrs(operation)) as span:
        try:
            yield span
        except Exception as e:
            span.record_exception(e)
            span.set_status(tracing.STATUS_ERROR, str(e))
            raise
        finally:
            logger.info("DB %-45s %.0fms", operation, (time.perf_counter() - t) * 1000)


async def _get_category_id(client: AsyncClient, name: str) -> int | None:
    async with _timed_db("categories.select(id).eq(name)") as span:
        response = await client.table("categories").select("id").eq("name", name).limit(1).execute()
        span.set_attribute("db.rows", len(response.data))
    if response.data:
        return response.data[0]["id"]
    return None


def _parse_expense_row(row: dict) -> Expense:
    row = dict(row)
    categories_data = row.pop("categories", None)
    row["category"] = categories_data["name"] if categories_data else ""
    return Expense(**row)


async def save_expense(expense: ExtractedExpense, category: str) -> str:
    client = await _get_client()
    category_id = await _get_category_id(client, category)
    record = {
        "amount": str(expense.amount),
        "date": expense.date.isoformat(),
        "establishment": expense.establishment,
        "description": expense.description,
        "category_id": category_id,
        "tax_id": expense.tax_id,
        "entry_type": expense.entry_type,
        "transaction_type": expense.transaction_type,
        "confidence": expense.confidence,
        "raw_data": expense.raw_data,
    }
    async with _timed_db("transactions.insert"):
        response = await client.table("transactions").insert(record).execute()
    return response.data[0]["id"]


async def get_recent_expenses(limit: int = 3) -> list[Expense]:
    client = await _get_client()
    async with _timed_db(f"transactions.select(*).order(created_at).limit({limit})") as span:
        response = (
            await client.table("transactions")
            .select("*, categories(name)")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        span.set_attribute("db.rows", len(response.data))
    return [_parse_expense_row(row) for row in response.data]


async def get_expenses_by_period(
    start: date,
    end: date,
    transaction_type: str | None = None,
) -> list[Expense]:
    client = await _get_client()
    async with _timed_db(f"transactions.select(*).period({start},{end})") as span:
        query = (
            client.table("transactions")
            .select("*, categories(name)")
            .gte("date", start.isoformat())
            .lte("date", end.isoformat())
        )
        if transaction_type is not None:
            query = query.eq("transaction_type", transaction_type)
        response = await query.order("date").execute()
        span.set_attribute("db.rows", len(response.data))
    return [_parse_expense_row(row) for row in response.data]


async def add_category(name: str) -> None:
    client = await _get_client()
    async with _timed_db("categories.insert"):
        await client.table("categories").insert({"name": name}).execute()


async def get_active_categories() -> list[str]:
    client = await _get_client()
    async with _timed_db("categories.select(name).eq(is_active=True)") as span:
        response = (
            await client.table("categories")
            .select("name")
            .eq("is_active", True)
            .order("name")
            .execute()
        )
        span.set_attribute("db.rows", len(response.data))
    return [row["name"] for row in response.data]


async def get_totals_by_category(
    start: date,
    end: date,
    transaction_type: str | None = None,
) -> dict[str, Decimal]:
    expenses = await get_expenses_by_period(start, end, transaction_type)
    totals: dict[str, Decimal] = {}
    for expense in expenses:
        totals[expense.category] = totals.get(expense.category, Decimal("0")) + expense.amount
    return totals


async def get_expenses_paginated(
    start: date | None,
    end: date | None,
    category_id: int | None,
    page: int,
    page_size: int,
    transaction_type: str | None = None,
) -> tuple[list[Expense], int]:
    client = await _get_client()
    query = client.table("transactions").select("*, categories(name)", count="exact")
    if start:
        query = query.gte("date", start.isoformat())
    if end:
        query = query.lte("date", end.isoformat())
    if category_id is not None:
        query = query.eq("category_id", category_id)
    if transaction_type is not None:
        query = query.eq("transaction_type", transaction_type)
    offset = (page - 1) * page_size
    query = query.order("date", desc=True).range(offset, offset + page_size - 1)
    async with _timed_db(f"transactions.select(*).paginated(page={page},size={page_size})") as span:
        response = await query.execute()
        span.set_attribute("db.rows", len(response.data))
    total = response.count or 0
    return [_parse_expense_row(row) for row in response.data], total


async def get_expense_by_id(expense_id: str) -> Expense | None:
    client = await _get_client()
    async with _timed_db(f"transactions.select(*).eq(id={expense_id[:8]}…)") as span:
        response = (
            await client.table("transactions")
            .select("*, categories(name)")
            .eq("id", expense_id)
            .limit(1)
            .execute()
        )
        span.set_attribute("db.rows", len(response.data))
    if not response.data:
        return None
    return _parse_expense_row(response.data[0])


async def create_expense_direct(record: dict) -> Expense:
    client = await _get_client()
    async with _timed_db("transactions.insert.select(*)"):
        response = (
            await client.table("transactions")
            .insert(record)
            .select("*, categories(name)")
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
            .select("*, categories(name)")
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
    async with _timed_db("categories.select(id,name,is_active).eq(is_active=True)") as span:
        response = (
            await client.table("categories")
            .select("id, name, is_active")
            .eq("is_active", True)
            .order("name")
            .execute()
        )
        span.set_attribute("db.rows", len(response.data))
    return response.data


async def create_category_full(name: str) -> dict:
    client = await _get_client()
    async with _timed_db("categories.insert.select(*)"):
        response = (
            await client.table("categories")
            .insert({"name": name})
            .select("id, name, is_active")
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
            .select("id, name, is_active")
            .execute()
        )
    if not response.data:
        return None
    return response.data[0]


async def deactivate_category(category_id: int) -> bool:
    client = await _get_client()
    async with _timed_db(f"categories.update(is_active=False).eq(id={category_id})"):
        response = (
            await client.table("categories")
            .update({"is_active": False})
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
