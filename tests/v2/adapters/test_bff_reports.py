from decimal import Decimal
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.v2.adapters.primary.bff.routers.bff_reports import router
from src.v2.domain.use_cases.reports.get_monthly import MonthlyByCategoryItem, MonthlyItem


def _app(use_cases: SimpleNamespace) -> FastAPI:
    app = FastAPI()
    app.state.use_cases = use_cases
    from src.v2.adapters.primary.bff import deps
    app.dependency_overrides[deps.get_current_user] = lambda: {"sub": "test-user"}
    app.include_router(router)
    return app


class StubGetMonthly:
    def __init__(self, expense_items: list[MonthlyItem], income_items: list[MonthlyItem] | None = None):
        self._expense_items = expense_items
        self._income_items = income_items if income_items is not None else []

    async def execute(self, query):
        if query.transaction_type == "income":
            return list(self._income_items)
        return list(self._expense_items)


def _expense_items():
    return [
        MonthlyItem(month=1, total=Decimal("369.40"), by_category=[
            MonthlyByCategoryItem(category="Alimentação", total=Decimal("245.90")),
        ]),
        MonthlyItem(month=3, total=Decimal("200.00"), by_category=[
            MonthlyByCategoryItem(category="Transporte", total=Decimal("200.00")),
        ]),
    ]


def _income_items():
    return [
        MonthlyItem(month=1, total=Decimal("5000.00"), by_category=[
            MonthlyByCategoryItem(category="Salário", total=Decimal("5000.00")),
        ]),
    ]


def test_bff_reports_combines_income_and_expense_by_month():
    uc = SimpleNamespace(get_monthly=StubGetMonthly(_expense_items(), _income_items()))
    client = TestClient(_app(uc))
    resp = client.get("/api/v2/bff/reports?year=2026")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 2  # months 1 and 3
    jan = next(m for m in body if m["month"] == 1)
    assert jan["expense_total"] == "369.40"
    assert jan["expense_by_category"][0]["category"] == "Alimentação"


def test_bff_reports_fills_zero_for_missing_type():
    # Month 3 has expenses but no income — income_total should be "0.00"
    uc = SimpleNamespace(get_monthly=StubGetMonthly(_expense_items()))
    client = TestClient(_app(uc))
    resp = client.get("/api/v2/bff/reports?year=2026")
    body = resp.json()
    mar = next(m for m in body if m["month"] == 3)
    assert mar["income_total"] == "0.00"
    assert mar["expense_total"] == "200.00"


def test_bff_reports_requires_year():
    uc = SimpleNamespace(get_monthly=StubGetMonthly([]))
    client = TestClient(_app(uc))
    resp = client.get("/api/v2/bff/reports")
    assert resp.status_code == 422


def test_bff_reports_empty_year():
    uc = SimpleNamespace(get_monthly=StubGetMonthly([]))
    client = TestClient(_app(uc))
    resp = client.get("/api/v2/bff/reports?year=2020")
    assert resp.status_code == 200
    assert resp.json() == []
