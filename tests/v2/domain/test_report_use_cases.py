import datetime as _dt
from decimal import Decimal
from uuid import uuid4

import pytest

from src.v2.domain.entities.expense import Expense, ExtractedExpense
from src.v2.domain.ports.expense_repository import (
    ExpenseFilters,
    ExpenseRepository,
    ExpenseUpdate,
)
from src.v2.domain.use_cases.reports.export_csv import ExportCsv, ExportCsvQuery
from src.v2.domain.use_cases.reports.get_monthly import GetMonthly, GetMonthlyQuery
from src.v2.domain.use_cases.reports.get_summary import GetSummary, GetSummaryQuery
from uuid import UUID


def _make_expense(category: str, amount: str, month: int) -> Expense:
    return Expense(
        id=uuid4(),
        amount=Decimal(amount),
        date=_dt.date(2026, month, 15),
        establishment="Store",
        description=None,
        category_id=1,
        category=category,
        tax_id=None,
        entry_type="text",
        transaction_type="expense",
        payment_method="debit",
        confidence=0.9,
        created_at=_dt.datetime(2026, month, 15, 10, 0),
    )


class StubExpenseRepository(ExpenseRepository):
    def __init__(self, expenses: list[Expense]):
        self._expenses = expenses

    async def save(self, expense: ExtractedExpense, category_id: int) -> Expense:
        raise NotImplementedError

    async def get_by_id(self, expense_id: UUID) -> Expense | None:
        raise NotImplementedError

    async def list_paginated(self, filters: ExpenseFilters) -> tuple[list[Expense], int]:
        raise NotImplementedError

    async def list_by_period(self, start, end, transaction_type=None) -> list[Expense]:
        return self._expenses

    async def get_recent(self, limit: int = 3) -> list[Expense]:
        raise NotImplementedError

    async def update(self, expense_id: UUID, data: ExpenseUpdate) -> Expense | None:
        raise NotImplementedError

    async def delete(self, expense_id: UUID) -> bool:
        raise NotImplementedError


@pytest.mark.asyncio
async def test_get_summary_aggregates_by_category():
    expenses = [
        _make_expense("Alimentação", "30.00", 1),
        _make_expense("Alimentação", "20.00", 1),
        _make_expense("Transporte", "15.00", 1),
    ]
    repo = StubExpenseRepository(expenses)
    result = await GetSummary(repo).execute(
        GetSummaryQuery(start=_dt.date(2026, 1, 1), end=_dt.date(2026, 1, 31))
    )
    by_cat = {item.category: item.total for item in result}
    assert by_cat["Alimentação"] == Decimal("50.00")
    assert by_cat["Transporte"] == Decimal("15.00")


@pytest.mark.asyncio
async def test_get_summary_returns_empty_for_no_expenses():
    repo = StubExpenseRepository([])
    result = await GetSummary(repo).execute(
        GetSummaryQuery(start=_dt.date(2026, 1, 1), end=_dt.date(2026, 1, 31))
    )
    assert result == []


@pytest.mark.asyncio
async def test_get_monthly_groups_by_month():
    expenses = [
        _make_expense("Alimentação", "100.00", 1),
        _make_expense("Transporte", "50.00", 2),
    ]
    repo = StubExpenseRepository(expenses)
    result = await GetMonthly(repo).execute(GetMonthlyQuery(year=2026))
    months = {item.month: item for item in result}
    assert months[1].total == Decimal("100.00")
    assert months[2].total == Decimal("50.00")


@pytest.mark.asyncio
async def test_export_csv_returns_utf8_bom_bytes():
    expenses = [_make_expense("Alimentação", "45.90", 1)]
    repo = StubExpenseRepository(expenses)
    result = await ExportCsv(repo).execute(
        ExportCsvQuery(start=_dt.date(2026, 1, 1), end=_dt.date(2026, 1, 31))
    )
    assert isinstance(result, bytes)
    # UTF-8 BOM for Excel compatibility
    assert result.startswith(b"\xef\xbb\xbf")
    content = result.decode("utf-8-sig")
    assert "Alimentação" in content
    assert "45.90" in content


@pytest.mark.asyncio
async def test_export_csv_has_header_row():
    repo = StubExpenseRepository([])
    result = await ExportCsv(repo).execute(
        ExportCsvQuery(start=_dt.date(2026, 1, 1), end=_dt.date(2026, 1, 31))
    )
    content = result.decode("utf-8-sig")
    assert "date" in content
    assert "amount" in content
    assert "category" in content
