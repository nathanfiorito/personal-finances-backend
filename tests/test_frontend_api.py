"""
Tests for the Frontend REST API (specs/frontend-api.spec.md).

Each test class maps to a domain (Auth, Expenses, Categories, Reports, Export).
The `override_auth` session-scoped fixture replaces the JWT guard globally;
auth-specific tests clear it to exercise the real dependency.
"""
import base64
import json
import time
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.models.expense import Expense
from src.routers.deps import get_current_user

client = TestClient(app)

# ---------------------------------------------------------------------------
# Shared test data
# ---------------------------------------------------------------------------

MOCK_USER = {"id": "test-user-id", "email": "test@example.com"}

MOCK_EXPENSE = Expense(
    id=UUID("12345678-1234-5678-1234-567812345678"),
    amount=Decimal("50.00"),
    date=date(2025, 1, 15),
    establishment="Mercado",
    description="Compras",
    category="Alimentação",
    category_id=1,
    tax_id=None,
    entry_type="texto",
    transaction_type="outcome",
    confidence=1.0,
    created_at=datetime(2025, 1, 15, 12, 0, 0),
)

MOCK_CATEGORY = {"id": 1, "name": "Alimentação", "is_active": True}

AUTH_HEADER = {"Authorization": "Bearer valid-token"}

EXPENSE_ID = "12345678-1234-5678-1234-567812345678"


def _make_jwt(exp: int) -> str:
    """Build a fake JWT with a known exp claim (no real signature)."""
    header = base64.b64encode(b'{"alg":"HS256"}').decode().rstrip("=")
    payload_bytes = json.dumps({"exp": exp, "sub": "user123"}).encode()
    payload = base64.b64encode(payload_bytes).decode().rstrip("=")
    return f"{header}.{payload}.fakesig"


EXPIRED_TOKEN = _make_jwt(int(time.time()) - 3600)
FRESH_TOKEN = _make_jwt(int(time.time()) + 3600)


# ---------------------------------------------------------------------------
# Auth override fixture (applied to all tests by default)
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def override_auth():
    app.dependency_overrides[get_current_user] = lambda: MOCK_USER
    yield
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# TestAuth — JWT validation (401 / 403)
# ---------------------------------------------------------------------------

class TestAuth:
    @pytest.fixture(autouse=True)
    def clear_auth_override(self):
        """Remove the global override so the real guard runs."""
        app.dependency_overrides.pop(get_current_user, None)
        yield
        app.dependency_overrides[get_current_user] = lambda: MOCK_USER

    def _mock_supabase_auth(self, mocker, *, side_effect):
        mock_client = MagicMock()
        mock_client.auth.get_user = AsyncMock(side_effect=side_effect)
        mocker.patch(
            "src.routers.deps._get_client",
            new_callable=AsyncMock,
            return_value=mock_client,
        )

    def test_missing_jwt_returns_401(self):
        # Arrange: no Authorization header
        # Act
        response = client.get("/api/transactions")
        # Assert
        assert response.status_code == 401

    def test_malformed_jwt_no_bearer_prefix_returns_401(self, mocker):
        # Arrange
        self._mock_supabase_auth(mocker, side_effect=Exception("invalid"))
        # Act
        response = client.get("/api/transactions", headers={"Authorization": "Token abc123"})
        # Assert
        assert response.status_code == 401

    def test_invalid_jwt_returns_401(self, mocker):
        # Arrange: Supabase rejects token, token is not expired
        self._mock_supabase_auth(mocker, side_effect=Exception("invalid jwt"))
        # Act
        response = client.get(
            "/api/transactions",
            headers={"Authorization": "Bearer bad-token-not-expired"},
        )
        # Assert
        assert response.status_code == 401

    def test_expired_jwt_returns_403(self, mocker):
        # Arrange: Supabase rejects token AND token payload shows exp in the past
        self._mock_supabase_auth(mocker, side_effect=Exception("expired"))
        # Act
        response = client.get(
            "/api/transactions",
            headers={"Authorization": f"Bearer {EXPIRED_TOKEN}"},
        )
        # Assert
        assert response.status_code == 403

    def test_valid_jwt_passes_through(self, mocker):
        # Arrange: Supabase accepts token
        mock_client = MagicMock()
        user_response = MagicMock()
        user_response.user = MOCK_USER
        mock_client.auth.get_user = AsyncMock(return_value=user_response)
        mocker.patch(
            "src.routers.deps._get_client",
            new_callable=AsyncMock,
            return_value=mock_client,
        )
        mocker.patch(
            "src.routers.transactions.database.get_expenses_paginated",
            new_callable=AsyncMock,
            return_value=([], 0),
        )
        # Act
        response = client.get(
            "/api/transactions",
            headers={"Authorization": f"Bearer {FRESH_TOKEN}"},
        )
        # Assert
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# TestExpenses
# ---------------------------------------------------------------------------

class TestExpenses:
    def test_list_expenses_no_filters_returns_paginated(self, mocker):
        # Arrange
        mocker.patch(
            "src.routers.transactions.database.get_expenses_paginated",
            new_callable=AsyncMock,
            return_value=([MOCK_EXPENSE], 1),
        )
        # Act
        response = client.get("/api/transactions", headers=AUTH_HEADER)
        # Assert
        assert response.status_code == 200
        body = response.json()
        assert body["total"] == 1
        assert body["page"] == 1
        assert body["page_size"] == 20
        assert len(body["items"]) == 1

    def test_list_expenses_filters_by_period(self, mocker):
        # Arrange
        mock_db = mocker.patch(
            "src.routers.transactions.database.get_expenses_paginated",
            new_callable=AsyncMock,
            return_value=([MOCK_EXPENSE], 1),
        )
        # Act
        response = client.get(
            "/api/transactions?start=2025-01-01&end=2025-01-31",
            headers=AUTH_HEADER,
        )
        # Assert
        assert response.status_code == 200
        call_kwargs = mock_db.call_args
        assert call_kwargs[0][0] == date(2025, 1, 1)
        assert call_kwargs[0][1] == date(2025, 1, 31)

    def test_list_expenses_filters_by_category_id(self, mocker):
        # Arrange
        mock_db = mocker.patch(
            "src.routers.transactions.database.get_expenses_paginated",
            new_callable=AsyncMock,
            return_value=([MOCK_EXPENSE], 1),
        )
        # Act
        response = client.get("/api/transactions?category_id=1", headers=AUTH_HEADER)
        # Assert
        assert response.status_code == 200
        assert mock_db.call_args[0][2] == 1

    def test_list_expenses_page_size_capped_at_100(self, mocker):
        # Arrange
        mock_db = mocker.patch(
            "src.routers.transactions.database.get_expenses_paginated",
            new_callable=AsyncMock,
            return_value=([], 0),
        )
        # Act
        response = client.get("/api/transactions?page_size=999", headers=AUTH_HEADER)
        # Assert
        assert response.status_code == 200
        assert mock_db.call_args[0][4] == 100

    def test_list_expenses_start_after_end_returns_422(self, mocker):
        # Arrange / Act
        response = client.get(
            "/api/transactions?start=2025-02-01&end=2025-01-01",
            headers=AUTH_HEADER,
        )
        # Assert
        assert response.status_code == 422

    def test_get_expense_by_id_returns_expense(self, mocker):
        # Arrange
        mocker.patch(
            "src.routers.transactions.database.get_expense_by_id",
            new_callable=AsyncMock,
            return_value=MOCK_EXPENSE,
        )
        # Act
        response = client.get(f"/api/transactions/{EXPENSE_ID}", headers=AUTH_HEADER)
        # Assert
        assert response.status_code == 200
        assert response.json()["id"] == EXPENSE_ID

    def test_get_expense_by_id_not_found_returns_404(self, mocker):
        # Arrange
        mocker.patch(
            "src.routers.transactions.database.get_expense_by_id",
            new_callable=AsyncMock,
            return_value=None,
        )
        # Act
        response = client.get(f"/api/transactions/{EXPENSE_ID}", headers=AUTH_HEADER)
        # Assert
        assert response.status_code == 404

    def test_create_expense_returns_201(self, mocker):
        # Arrange
        mocker.patch(
            "src.routers.transactions.database.create_expense_direct",
            new_callable=AsyncMock,
            return_value=MOCK_EXPENSE,
        )
        body = {
            "amount": "50.00",
            "date": "2025-01-15",
            "establishment": "Mercado",
            "category_id": 1,
            "entry_type": "texto",
        }
        # Act
        response = client.post("/api/transactions", json=body, headers=AUTH_HEADER)
        # Assert
        assert response.status_code == 201
        assert response.json()["id"] == EXPENSE_ID

    def test_create_expense_amount_zero_returns_422(self, mocker):
        # Arrange
        body = {"amount": "0", "date": "2025-01-15", "category_id": 1, "entry_type": "texto"}
        # Act
        response = client.post("/api/transactions", json=body, headers=AUTH_HEADER)
        # Assert
        assert response.status_code == 422

    def test_create_expense_amount_too_large_returns_422(self, mocker):
        # Arrange
        body = {"amount": "1000000", "date": "2025-01-15", "category_id": 1, "entry_type": "texto"}
        # Act
        response = client.post("/api/transactions", json=body, headers=AUTH_HEADER)
        # Assert
        assert response.status_code == 422

    def test_update_expense_returns_updated(self, mocker):
        # Arrange
        updated = MOCK_EXPENSE.model_copy(update={"establishment": "Padaria"})
        mocker.patch(
            "src.routers.transactions.database.update_expense",
            new_callable=AsyncMock,
            return_value=updated,
        )
        # Act
        response = client.put(
            f"/api/transactions/{EXPENSE_ID}",
            json={"establishment": "Padaria"},
            headers=AUTH_HEADER,
        )
        # Assert
        assert response.status_code == 200
        assert response.json()["establishment"] == "Padaria"

    def test_update_expense_not_found_returns_404(self, mocker):
        # Arrange
        mocker.patch(
            "src.routers.transactions.database.update_expense",
            new_callable=AsyncMock,
            return_value=None,
        )
        # Act
        response = client.put(
            f"/api/transactions/{EXPENSE_ID}",
            json={"establishment": "Padaria"},
            headers=AUTH_HEADER,
        )
        # Assert
        assert response.status_code == 404

    def test_delete_expense_returns_204(self, mocker):
        # Arrange
        mocker.patch(
            "src.routers.transactions.database.delete_expense",
            new_callable=AsyncMock,
            return_value=True,
        )
        # Act
        response = client.delete(f"/api/transactions/{EXPENSE_ID}", headers=AUTH_HEADER)
        # Assert
        assert response.status_code == 204

    def test_delete_expense_not_found_returns_404(self, mocker):
        # Arrange
        mocker.patch(
            "src.routers.transactions.database.delete_expense",
            new_callable=AsyncMock,
            return_value=False,
        )
        # Act
        response = client.delete(f"/api/transactions/{EXPENSE_ID}", headers=AUTH_HEADER)
        # Assert
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# TestCategories
# ---------------------------------------------------------------------------

class TestCategories:
    def test_list_categories_returns_active_only(self, mocker):
        # Arrange: DB returns only active categories (filter is in DB layer)
        mocker.patch(
            "src.routers.categories.database.get_all_categories",
            new_callable=AsyncMock,
            return_value=[MOCK_CATEGORY],
        )
        # Act
        response = client.get("/api/categories", headers=AUTH_HEADER)
        # Assert
        assert response.status_code == 200
        assert response.json() == [MOCK_CATEGORY]

    def test_create_category_returns_201(self, mocker):
        # Arrange
        mocker.patch(
            "src.routers.categories.database.create_category_full",
            new_callable=AsyncMock,
            return_value=MOCK_CATEGORY,
        )
        # Act
        response = client.post("/api/categories", json={"name": "Alimentação"}, headers=AUTH_HEADER)
        # Assert
        assert response.status_code == 201
        assert response.json()["name"] == "Alimentação"

    def test_create_category_duplicate_returns_409(self, mocker):
        # Arrange
        mocker.patch(
            "src.routers.categories.database.create_category_full",
            new_callable=AsyncMock,
            side_effect=Exception("duplicate key value violates unique constraint"),
        )
        # Act
        response = client.post("/api/categories", json={"name": "Alimentação"}, headers=AUTH_HEADER)
        # Assert
        assert response.status_code == 409

    def test_update_category_partial_patch(self, mocker):
        # Arrange
        updated = {**MOCK_CATEGORY, "name": "Alimentação e Bebidas"}
        mocker.patch(
            "src.routers.categories.database.update_category",
            new_callable=AsyncMock,
            return_value=updated,
        )
        # Act
        response = client.patch(
            "/api/categories/1",
            json={"name": "Alimentação e Bebidas"},
            headers=AUTH_HEADER,
        )
        # Assert
        assert response.status_code == 200
        assert response.json()["name"] == "Alimentação e Bebidas"

    def test_update_category_not_found_returns_404(self, mocker):
        # Arrange
        mocker.patch(
            "src.routers.categories.database.update_category",
            new_callable=AsyncMock,
            return_value=None,
        )
        # Act
        response = client.patch("/api/categories/99", json={"name": "X"}, headers=AUTH_HEADER)
        # Assert
        assert response.status_code == 404

    def test_deactivate_category_returns_204(self, mocker):
        # Arrange
        mocker.patch(
            "src.routers.categories.database.deactivate_category",
            new_callable=AsyncMock,
            return_value=True,
        )
        # Act
        response = client.delete("/api/categories/1", headers=AUTH_HEADER)
        # Assert: desativa (não remove) e retorna 204
        assert response.status_code == 204

    def test_deactivate_category_not_found_returns_404(self, mocker):
        # Arrange
        mocker.patch(
            "src.routers.categories.database.deactivate_category",
            new_callable=AsyncMock,
            return_value=False,
        )
        # Act
        response = client.delete("/api/categories/99", headers=AUTH_HEADER)
        # Assert
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# TestReports
# ---------------------------------------------------------------------------

class TestReports:
    def _make_expense(self, month: int, category: str, amount: str) -> Expense:
        return MOCK_EXPENSE.model_copy(
            update={
                "date": date(2025, month, 1),
                "category": category,
                "amount": Decimal(amount),
            }
        )

    def test_summary_returns_totals_sorted_desc(self, mocker):
        # Arrange
        mocker.patch(
            "src.routers.reports.database.get_totals_by_category",
            new_callable=AsyncMock,
            return_value={
                "Transporte": Decimal("30.00"),
                "Alimentação": Decimal("200.00"),
                "Lazer": Decimal("80.00"),
            },
        )
        # Act
        response = client.get(
            "/api/reports/summary?start=2025-01-01&end=2025-01-31",
            headers=AUTH_HEADER,
        )
        # Assert
        assert response.status_code == 200
        body = response.json()
        assert body[0]["category"] == "Alimentação"
        assert body[1]["category"] == "Lazer"
        assert body[2]["category"] == "Transporte"

    def test_summary_missing_params_returns_422(self):
        # Arrange / Act
        response = client.get("/api/reports/summary", headers=AUTH_HEADER)
        # Assert
        assert response.status_code == 422

    def test_summary_start_after_end_returns_422(self, mocker):
        # Act
        response = client.get(
            "/api/reports/summary?start=2025-02-01&end=2025-01-01",
            headers=AUTH_HEADER,
        )
        # Assert
        assert response.status_code == 422

    def test_monthly_returns_breakdown_by_month(self, mocker):
        # Arrange
        expenses = [
            self._make_expense(1, "Alimentação", "100.00"),
            self._make_expense(1, "Transporte", "30.00"),
            self._make_expense(3, "Lazer", "50.00"),
        ]
        mocker.patch(
            "src.routers.reports.database.get_expenses_by_year",
            new_callable=AsyncMock,
            return_value=expenses,
        )
        # Act
        response = client.get("/api/reports/monthly?year=2025", headers=AUTH_HEADER)
        # Assert
        assert response.status_code == 200
        body = response.json()
        months = [item["month"] for item in body]
        assert months == [1, 3]  # only months with expenses
        jan = next(item for item in body if item["month"] == 1)
        assert float(jan["total"]) == 130.0

    def test_monthly_defaults_to_current_year(self, mocker):
        # Arrange
        mock_db = mocker.patch(
            "src.routers.reports.database.get_expenses_by_year",
            new_callable=AsyncMock,
            return_value=[],
        )
        # Act
        response = client.get("/api/reports/monthly", headers=AUTH_HEADER)
        # Assert
        assert response.status_code == 200
        from datetime import datetime
        current_year = datetime.now().year
        mock_db.assert_called_once_with(current_year, None)


# ---------------------------------------------------------------------------
# TestExport
# ---------------------------------------------------------------------------

class TestExport:
    def test_csv_export_returns_file(self, mocker):
        # Arrange
        mocker.patch(
            "src.routers.export.database.get_expenses_by_period",
            new_callable=AsyncMock,
            return_value=[MOCK_EXPENSE],
        )
        # Act
        response = client.get(
            "/api/export/csv?start=2025-01-01&end=2025-01-31",
            headers=AUTH_HEADER,
        )
        # Assert
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/csv")
        assert "attachment" in response.headers["content-disposition"]
        assert "expenses_2025-01-01_2025-01-31.csv" in response.headers["content-disposition"]

    def test_csv_export_has_correct_columns(self, mocker):
        # Arrange
        mocker.patch(
            "src.routers.export.database.get_expenses_by_period",
            new_callable=AsyncMock,
            return_value=[MOCK_EXPENSE],
        )
        # Act
        response = client.get(
            "/api/export/csv?start=2025-01-01&end=2025-01-31",
            headers=AUTH_HEADER,
        )
        # Assert
        lines = response.text.strip().splitlines()
        header = lines[0]
        expected_cols = ["id", "date", "establishment", "description", "category", "amount", "tax_id", "entry_type", "confidence", "created_at"]
        for col in expected_cols:
            assert col in header

    def test_csv_export_missing_params_returns_422(self):
        # Arrange / Act
        response = client.get("/api/export/csv", headers=AUTH_HEADER)
        # Assert
        assert response.status_code == 422

    def test_csv_export_start_after_end_returns_422(self, mocker):
        # Act
        response = client.get(
            "/api/export/csv?start=2025-02-01&end=2025-01-01",
            headers=AUTH_HEADER,
        )
        # Assert
        assert response.status_code == 422

    def test_csv_export_empty_period_returns_empty_csv(self, mocker):
        # Arrange
        mocker.patch(
            "src.routers.export.database.get_expenses_by_period",
            new_callable=AsyncMock,
            return_value=[],
        )
        # Act
        response = client.get(
            "/api/export/csv?start=2025-01-01&end=2025-01-31",
            headers=AUTH_HEADER,
        )
        # Assert
        assert response.status_code == 200
        lines = response.text.strip().splitlines()
        assert len(lines) == 1  # only header row
