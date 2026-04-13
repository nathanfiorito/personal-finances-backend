from __future__ import annotations

import datetime as _dt
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

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
        transaction_type="expense",
        payment_method="debit",
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


def test_create_transaction_returns_201():
    uc = SimpleNamespace(
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
            "transaction_type": "expense",
            "payment_method": "debit",
        },
    )
    assert resp.status_code == 201


def test_create_transaction_with_payment_method_returns_201():
    uc = SimpleNamespace(
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
            "entry_type": "manual",
            "transaction_type": "expense",
            "payment_method": "credit",
        },
    )
    assert resp.status_code == 201


def test_create_transaction_without_payment_method_returns_422():
    uc = SimpleNamespace(
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
            "entry_type": "manual",
            "transaction_type": "expense",
        },
    )
    assert resp.status_code == 422


def test_update_transaction_returns_404_when_not_found():
    uc = SimpleNamespace(
        create_expense=StubCreateExpense(),
        update_expense=StubUpdateExpense(found=False),
        delete_expense=StubDeleteExpense(),
    )
    client = TestClient(_app(uc))
    resp = client.put(
        f"/api/v2/transactions/{uuid4()}",
        json={"amount": "10.00"},
    )
    assert resp.status_code == 404


def test_delete_transaction_returns_204():
    expense = _make_expense()

    class DeleteStub:
        async def execute(self, cmd):
            pass

    uc = SimpleNamespace(
        create_expense=StubCreateExpense(),
        update_expense=StubUpdateExpense(),
        delete_expense=DeleteStub(),
    )
    client = TestClient(_app(uc))
    resp = client.delete(f"/api/v2/transactions/{expense.id}")
    assert resp.status_code == 204
