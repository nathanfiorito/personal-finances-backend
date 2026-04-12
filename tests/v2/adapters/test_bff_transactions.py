import datetime as _dt
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.v2.adapters.primary.bff.routers.transactions import router
from src.v2.domain.entities.expense import Expense
from src.v2.domain.exceptions import ExpenseNotFoundError


def _make_expense() -> Expense:
    return Expense(
        id=uuid4(),
        amount=Decimal("50.00"),
        date=_dt.date(2026, 1, 15),
        establishment="Store",
        description=None,
        category_id=1,
        category="Alimentação",
        tax_id=None,
        entry_type="text",
        transaction_type="outcome",
        confidence=0.9,
        created_at=_dt.datetime(2026, 1, 15, 10, 0),
    )


def _app(use_cases: SimpleNamespace) -> FastAPI:
    app = FastAPI()
    app.state.use_cases = use_cases

    from src.v2.adapters.primary.bff import deps
    app.dependency_overrides[deps.get_current_user] = lambda: {"sub": "test-user"}
    app.include_router(router)
    return app


class StubListExpenses:
    async def execute(self, query):
        return [_make_expense()], 1


class StubGetExpense:
    def __init__(self, found: bool = True):
        self._found = found

    async def execute(self, query):
        if not self._found:
            raise ExpenseNotFoundError("not found")
        return _make_expense()


class StubCreateExpense:
    async def execute(self, cmd):
        return _make_expense()


class StubUpdateExpense:
    def __init__(self, found: bool = True):
        self._found = found

    async def execute(self, cmd):
        if not self._found:
            raise ExpenseNotFoundError("not found")
        return _make_expense()


class StubDeleteExpense:
    def __init__(self, found: bool = True):
        self._found = found

    async def execute(self, cmd):
        if not self._found:
            raise ExpenseNotFoundError("not found")


def test_list_transactions_returns_200():
    uc = SimpleNamespace(
        list_expenses=StubListExpenses(),
        get_expense=StubGetExpense(),
        create_expense=StubCreateExpense(),
        update_expense=StubUpdateExpense(),
        delete_expense=StubDeleteExpense(),
    )
    client = TestClient(_app(uc))
    resp = client.get("/api/v2/transactions")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert len(body["items"]) == 1


def test_get_transaction_returns_200_when_found():
    expense = _make_expense()

    class FoundStub:
        async def execute(self, q):
            return expense

    uc = SimpleNamespace(
        list_expenses=StubListExpenses(),
        get_expense=FoundStub(),
        create_expense=StubCreateExpense(),
        update_expense=StubUpdateExpense(),
        delete_expense=StubDeleteExpense(),
    )
    client = TestClient(_app(uc))
    resp = client.get(f"/api/v2/transactions/{expense.id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == str(expense.id)


def test_get_transaction_returns_404_when_not_found():
    uc = SimpleNamespace(
        list_expenses=StubListExpenses(),
        get_expense=StubGetExpense(found=False),
        create_expense=StubCreateExpense(),
        update_expense=StubUpdateExpense(),
        delete_expense=StubDeleteExpense(),
    )
    client = TestClient(_app(uc))
    resp = client.get(f"/api/v2/transactions/{uuid4()}")
    assert resp.status_code == 404


def test_create_transaction_returns_201():
    uc = SimpleNamespace(
        list_expenses=StubListExpenses(),
        get_expense=StubGetExpense(),
        create_expense=StubCreateExpense(),
        update_expense=StubUpdateExpense(),
        delete_expense=StubDeleteExpense(),
    )
    client = TestClient(_app(uc))
    resp = client.post(
        "/api/v2/transactions",
        json={
            "amount": "50.00",
            "date": "2026-01-15",
            "category_id": 1,
            "entry_type": "text",
            "transaction_type": "outcome",
        },
    )
    assert resp.status_code == 201


def test_delete_transaction_returns_204():
    expense = _make_expense()

    class DeleteStub:
        async def execute(self, cmd):
            pass

    uc = SimpleNamespace(
        list_expenses=StubListExpenses(),
        get_expense=StubGetExpense(),
        create_expense=StubCreateExpense(),
        update_expense=StubUpdateExpense(),
        delete_expense=DeleteStub(),
    )
    client = TestClient(_app(uc))
    resp = client.delete(f"/api/v2/transactions/{expense.id}")
    assert resp.status_code == 204
