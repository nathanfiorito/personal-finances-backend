from decimal import Decimal
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.v2.adapters.primary.bff.routers.bff_dashboard import router
from src.v2.domain.use_cases.reports.get_summary import SummaryItem


def _app(use_cases: SimpleNamespace) -> FastAPI:
    app = FastAPI()
    app.state.use_cases = use_cases
    from src.v2.adapters.primary.bff import deps
    app.dependency_overrides[deps.get_current_user] = lambda: {"sub": "test-user"}
    app.include_router(router)
    return app


class StubGetSummary:
    async def execute(self, query):
        if query.transaction_type == "income":
            return [SummaryItem(category="Salário", total=Decimal("3000.00"), count=1)]
        return [SummaryItem(category="Alimentação", total=Decimal("245.90"), count=4)]


def _default_uc():
    return SimpleNamespace(get_summary=StubGetSummary())


def test_dashboard_returns_200_with_aggregated_data():
    client = TestClient(_app(_default_uc()))
    resp = client.get("/api/v2/bff/dashboard?start=2026-01-01&end=2026-01-31")
    assert resp.status_code == 200
    body = resp.json()
    assert "expense_summary" in body
    assert "income_summary" in body
    assert body["transaction_count"] == 5  # 4 expense + 1 income
    assert body["expense_summary"][0]["category"] == "Alimentação"
    assert body["expense_summary"][0]["total"] == "245.90"


def test_dashboard_requires_start_and_end():
    client = TestClient(_app(_default_uc()))
    resp = client.get("/api/v2/bff/dashboard?start=2026-01-01")
    assert resp.status_code == 422


def test_dashboard_returns_422_when_start_after_end():
    client = TestClient(_app(_default_uc()))
    resp = client.get("/api/v2/bff/dashboard?start=2026-02-01&end=2026-01-01")
    assert resp.status_code == 422
