import logging
import time
from datetime import date
from decimal import Decimal
from uuid import UUID

from supabase import AsyncClient

from src.v2.domain.entities.expense import Expense, ExtractedExpense
from src.v2.domain.ports.expense_repository import (
    ExpenseFilters,
    ExpenseRepository,
    ExpenseUpdate,
)

logger = logging.getLogger(__name__)

_TABLE = "transactions"


def _parse_row(row: dict) -> Expense:
    row = dict(row)
    categories_data = row.pop("categories", None)
    row["category"] = categories_data["name"] if categories_data else ""
    return Expense(**row)


class SupabaseExpenseRepository(ExpenseRepository):
    def __init__(self, client: AsyncClient) -> None:
        self._client = client

    async def save(self, expense: ExtractedExpense, category_id: int) -> Expense:
        record = {
            "amount": str(expense.amount),
            "date": expense.date.isoformat() if expense.date else None,
            "establishment": expense.establishment,
            "description": expense.description,
            "category_id": category_id,
            "tax_id": expense.tax_id,
            "entry_type": expense.entry_type,
            "transaction_type": expense.transaction_type,
            "confidence": expense.confidence,
            "raw_data": {},
        }
        t = time.perf_counter()
        response = (
            await self._client.table(_TABLE)
            .insert(record)
            .select("*, categories(name)")
            .execute()
        )
        logger.info("DB %s.insert %.0fms", _TABLE, (time.perf_counter() - t) * 1000)
        return _parse_row(response.data[0])

    async def get_by_id(self, expense_id: UUID) -> Expense | None:
        t = time.perf_counter()
        response = (
            await self._client.table(_TABLE)
            .select("*, categories(name)")
            .eq("id", str(expense_id))
            .limit(1)
            .execute()
        )
        logger.info("DB %s.get_by_id %.0fms", _TABLE, (time.perf_counter() - t) * 1000)
        if not response.data:
            return None
        return _parse_row(response.data[0])

    async def list_paginated(
        self, filters: ExpenseFilters
    ) -> tuple[list[Expense], int]:
        query = self._client.table(_TABLE).select(
            "*, categories(name)", count="exact"
        )
        if filters.start:
            query = query.gte("date", filters.start.isoformat())
        if filters.end:
            query = query.lte("date", filters.end.isoformat())
        if filters.category_id is not None:
            query = query.eq("category_id", filters.category_id)
        if filters.transaction_type is not None:
            query = query.eq("transaction_type", filters.transaction_type)
        offset = (filters.page - 1) * filters.page_size
        query = query.order("date", desc=True).range(
            offset, offset + filters.page_size - 1
        )
        t = time.perf_counter()
        response = await query.execute()
        logger.info(
            "DB %s.list_paginated(page=%d) %.0fms",
            _TABLE, filters.page, (time.perf_counter() - t) * 1000,
        )
        total = response.count or 0
        return [_parse_row(row) for row in response.data], total

    async def list_by_period(
        self,
        start: date,
        end: date,
        transaction_type: str | None = None,
    ) -> list[Expense]:
        query = (
            self._client.table(_TABLE)
            .select("*, categories(name)")
            .gte("date", start.isoformat())
            .lte("date", end.isoformat())
        )
        if transaction_type is not None:
            query = query.eq("transaction_type", transaction_type)
        t = time.perf_counter()
        response = await query.order("date").execute()
        logger.info(
            "DB %s.list_by_period(%s..%s) %.0fms",
            _TABLE, start, end, (time.perf_counter() - t) * 1000,
        )
        return [_parse_row(row) for row in response.data]

    async def get_recent(self, limit: int = 3) -> list[Expense]:
        t = time.perf_counter()
        response = (
            await self._client.table(_TABLE)
            .select("*, categories(name)")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        logger.info(
            "DB %s.get_recent(limit=%d) %.0fms",
            _TABLE, limit, (time.perf_counter() - t) * 1000,
        )
        return [_parse_row(row) for row in response.data]

    async def update(self, expense_id: UUID, data: ExpenseUpdate) -> Expense | None:
        payload = {
            k: v
            for k, v in {
                "amount": str(data.amount) if data.amount is not None else None,
                "date": data.date.isoformat() if data.date else None,
                "establishment": data.establishment,
                "description": data.description,
                "category_id": data.category_id,
                "tax_id": data.tax_id,
                "entry_type": data.entry_type,
                "transaction_type": data.transaction_type,
            }.items()
            if v is not None
        }
        if not payload:
            return await self.get_by_id(expense_id)
        t = time.perf_counter()
        response = (
            await self._client.table(_TABLE)
            .update(payload)
            .eq("id", str(expense_id))
            .select("*, categories(name)")
            .execute()
        )
        logger.info(
            "DB %s.update %.0fms", _TABLE, (time.perf_counter() - t) * 1000
        )
        if not response.data:
            return None
        return _parse_row(response.data[0])

    async def delete(self, expense_id: UUID) -> bool:
        t = time.perf_counter()
        response = (
            await self._client.table(_TABLE)
            .delete()
            .eq("id", str(expense_id))
            .select("id")
            .execute()
        )
        logger.info(
            "DB %s.delete %.0fms", _TABLE, (time.perf_counter() - t) * 1000
        )
        return bool(response.data)
