from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.v2.adapters.primary.bff.routers.export import router as export_router
from src.v2.adapters.primary.bff.routers.reports import router as reports_router
from src.v2.domain.use_cases.reports.get_monthly import MonthlyByCategoryItem, MonthlyItem


def _app(use_cases: SimpleNamespace) -> FastAPI:
    app = FastAPI()
    app.state.use_cases = use_cases
    from src.v2.adapters.primary.bff import deps
    app.dependency_overrides[deps.get_current_user] = lambda: {"sub": "test-user"}
    app.include_router(reports_router)
    app.include_router(export_router)
    return app


class StubGetMonthly:
    async def execute(self, query):
        return [
            MonthlyItem(
                month=1,
                total=Decimal("369.40"),
                by_category=[
                    MonthlyByCategoryItem(category="Alimentação", total=Decimal("245.90")),
                ],
            )
        ]


class StubExportCsv:
    async def execute(self, query):
        return b"\xef\xbb\xbfdate,amount\n2024-01-15,50.00\n"


def _default_uc():
    return SimpleNamespace(
        get_monthly=StubGetMonthly(),
        export_csv=StubExportCsv(),
    )


class TestMonthly:
    def test_returns_200_with_monthly_items(self):
        client = TestClient(_app(_default_uc()))
        resp = client.get("/api/v2/reports/monthly?year=2024")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["month"] == 1
        assert data[0]["total"] == "369.40"
        assert data[0]["by_category"][0]["category"] == "Alimentação"

    def test_requires_year(self):
        client = TestClient(_app(_default_uc()))
        resp = client.get("/api/v2/reports/monthly")
        assert resp.status_code == 422


class TestExportCsv:
    def test_returns_csv_content(self):
        client = TestClient(_app(_default_uc()))
        resp = client.get("/api/v2/export/csv?start=2024-01-01&end=2024-01-31")
        assert resp.status_code == 200
        assert "text/csv" in resp.headers["content-type"]
        assert "attachment" in resp.headers["content-disposition"]
        assert "expenses_2024-01-01_2024-01-31.csv" in resp.headers["content-disposition"]

    def test_requires_start_and_end(self):
        client = TestClient(_app(_default_uc()))
        resp = client.get("/api/v2/export/csv?start=2024-01-01")
        assert resp.status_code == 422
