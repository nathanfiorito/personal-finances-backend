import datetime as _dt
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.v2.adapters.primary.bff.routers.bff_expenses import router
from src.v2.domain.entities.category import Category
from src.v2.domain.entities.expense import Expense


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


class StubListExpenses:
    async def execute(self, query):
        return [_make_expense()], 1


class StubListCategories:
    async def execute(self):
        return [Category(id=1, name="Alimentação", is_active=True)]


def _default_uc():
    return SimpleNamespace(
        list_expenses=StubListExpenses(),
        list_categories=StubListCategories(),
    )


def test_expenses_page_returns_200_with_transactions_and_categories():
    client = TestClient(_app(_default_uc()))
    resp = client.get("/api/v2/bff/expenses")
    assert resp.status_code == 200
    body = resp.json()
    assert "transactions" in body
    assert "categories" in body
    assert body["transactions"]["total"] == 1
    assert len(body["transactions"]["items"]) == 1
    assert len(body["categories"]) == 1
    assert body["categories"][0]["name"] == "Alimentação"


def test_expenses_page_passes_filters_to_list_uc():
    received = {}

    class CapturingListExpenses:
        async def execute(self, query):
            received["query"] = query
            return [], 0

    uc = SimpleNamespace(
        list_expenses=CapturingListExpenses(),
        list_categories=StubListCategories(),
    )
    client = TestClient(_app(uc))
    client.get("/api/v2/bff/expenses?category_id=2&page=2&page_size=10")
    assert received["query"].category_id == 2
    assert received["query"].page == 2
    assert received["query"].page_size == 10
