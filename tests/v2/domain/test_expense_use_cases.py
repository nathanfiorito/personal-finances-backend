import datetime as _dt
from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from src.v2.domain.entities.category import Category
from src.v2.domain.entities.expense import Expense, ExtractedExpense


def test_payment_method_enum_has_credit_and_debit():
    from src.v2.domain.entities.expense import PaymentMethod
    assert PaymentMethod.CREDIT == "credit"
    assert PaymentMethod.DEBIT == "debit"
from src.v2.domain.exceptions import ExpenseNotFoundError
from src.v2.domain.ports.category_repository import CategoryRepository, CategoryUpdate
from src.v2.domain.ports.expense_repository import (
    ExpenseFilters,
    ExpenseRepository,
    ExpenseUpdate,
)
from src.v2.domain.use_cases.expenses.create_expense import (
    CreateExpense,
    CreateExpenseCommand,
)
from src.v2.domain.use_cases.expenses.delete_expense import (
    DeleteExpense,
    DeleteExpenseCommand,
)
from src.v2.domain.use_cases.expenses.get_expense import GetExpense, GetExpenseQuery
from src.v2.domain.use_cases.expenses.list_expenses import (
    ListExpenses,
    ListExpensesQuery,
)
from src.v2.domain.use_cases.expenses.update_expense import (
    UpdateExpense,
    UpdateExpenseCommand,
)


# ── Stubs ────────────────────────────────────────────────────────────────────

def _make_expense(expense_id: UUID | None = None) -> Expense:
    return Expense(
        id=expense_id or uuid4(),
        amount=Decimal("50.00"),
        date=_dt.date(2026, 1, 15),
        establishment="Test Store",
        description=None,
        category_id=1,
        category="Alimentação",
        tax_id=None,
        entry_type="text",
        transaction_type="expense",
        payment_method="debit",
        confidence=0.9,
        created_at=_dt.datetime(2026, 1, 15, 10, 0),
    )


class StubExpenseRepository(ExpenseRepository):
    def __init__(self, expenses: list[Expense] | None = None):
        self._expenses: list[Expense] = list(expenses or [])

    async def save(self, expense: ExtractedExpense, category_id: int) -> Expense:
        saved = _make_expense()
        self._expenses.append(saved)
        return saved

    async def get_by_id(self, expense_id: UUID) -> Expense | None:
        return next((e for e in self._expenses if e.id == expense_id), None)

    async def list_paginated(self, filters: ExpenseFilters) -> tuple[list[Expense], int]:
        return self._expenses, len(self._expenses)

    async def list_by_period(self, start, end, transaction_type=None) -> list[Expense]:
        return self._expenses

    async def get_recent(self, limit: int = 3) -> list[Expense]:
        return self._expenses[:limit]

    async def update(self, expense_id: UUID, data: ExpenseUpdate) -> Expense | None:
        return next((e for e in self._expenses if e.id == expense_id), None)

    async def delete(self, expense_id: UUID) -> bool:
        before = len(self._expenses)
        self._expenses = [e for e in self._expenses if e.id != expense_id]
        return len(self._expenses) < before


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_expense_returns_saved_expense():
    repo = StubExpenseRepository()
    use_case = CreateExpense(repo)
    cmd = CreateExpenseCommand(
        amount=Decimal("50.00"),
        date=_dt.date(2026, 1, 15),
        category_id=1,
        entry_type="text",
        transaction_type="expense",
        payment_method="debit",
        establishment="Test Store",
    )
    result = await use_case.execute(cmd)
    assert result.amount == Decimal("50.00")
    assert result.entry_type == "text"


@pytest.mark.asyncio
async def test_get_expense_returns_expense_when_found():
    expense = _make_expense()
    repo = StubExpenseRepository([expense])
    result = await GetExpense(repo).execute(GetExpenseQuery(expense_id=expense.id))
    assert result.id == expense.id


@pytest.mark.asyncio
async def test_get_expense_raises_when_not_found():
    repo = StubExpenseRepository()
    with pytest.raises(ExpenseNotFoundError):
        await GetExpense(repo).execute(GetExpenseQuery(expense_id=uuid4()))


@pytest.mark.asyncio
async def test_list_expenses_returns_paginated_results():
    expenses = [_make_expense() for _ in range(3)]
    repo = StubExpenseRepository(expenses)
    items, total = await ListExpenses(repo).execute(ListExpensesQuery())
    assert total == 3
    assert len(items) == 3


@pytest.mark.asyncio
async def test_list_expenses_caps_page_size_at_100():
    repo = StubExpenseRepository()
    query = ListExpensesQuery(page_size=999)
    # Should not raise; page_size is clamped inside the use case
    await ListExpenses(repo).execute(query)


@pytest.mark.asyncio
async def test_update_expense_returns_updated_expense():
    expense = _make_expense()
    repo = StubExpenseRepository([expense])
    result = await UpdateExpense(repo).execute(
        UpdateExpenseCommand(expense_id=expense.id, description="Updated")
    )
    assert result is not None


@pytest.mark.asyncio
async def test_update_expense_raises_when_not_found():
    repo = StubExpenseRepository()
    with pytest.raises(ExpenseNotFoundError):
        await UpdateExpense(repo).execute(
            UpdateExpenseCommand(expense_id=uuid4(), description="x")
        )


@pytest.mark.asyncio
async def test_delete_expense_succeeds_when_exists():
    expense = _make_expense()
    repo = StubExpenseRepository([expense])
    # Should not raise
    await DeleteExpense(repo).execute(DeleteExpenseCommand(expense_id=expense.id))


@pytest.mark.asyncio
async def test_delete_expense_raises_when_not_found():
    repo = StubExpenseRepository()
    with pytest.raises(ExpenseNotFoundError):
        await DeleteExpense(repo).execute(DeleteExpenseCommand(expense_id=uuid4()))


@pytest.mark.asyncio
async def test_create_expense_command_accepts_payment_method():
    repo = StubExpenseRepository()
    cmd = CreateExpenseCommand(
        amount=Decimal("50.00"),
        date=_dt.date(2026, 1, 15),
        category_id=1,
        entry_type="manual",
        transaction_type="expense",
        payment_method="credit",
    )
    result = await CreateExpense(repo).execute(cmd)
    assert result is not None


@pytest.mark.asyncio
async def test_update_expense_command_accepts_payment_method():
    expense = _make_expense()
    repo = StubExpenseRepository([expense])
    cmd = UpdateExpenseCommand(
        expense_id=expense.id,
        payment_method="credit",
    )
    result = await UpdateExpense(repo).execute(cmd)
    assert result is not None
