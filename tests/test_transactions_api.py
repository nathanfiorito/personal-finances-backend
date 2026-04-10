"""
Tests for the Transactions API (specs/spec-03-income-and-outcome.spec.md).

Covers:
- GET /api/transactions — list with transaction_type filter
- POST /api/transactions — transaction_type required, validated
- PUT /api/transactions/{id} — transaction_type updatable
- GET /api/transactions/{id}
- DELETE /api/transactions/{id}
- GET /api/expenses/* — 301 redirect to /api/transactions/*
- Reports: GET /api/reports/summary with transaction_type filter
"""
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, patch
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.models.expense import Expense
from src.routers.deps import get_current_user

client = TestClient(app, follow_redirects=False)

MOCK_USER = {"id": "test-user-id", "email": "test@example.com"}

MOCK_OUTCOME = Expense(
    id=UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
    amount=Decimal("120.00"),
    date=date(2025, 3, 10),
    establishment="Supermercado Extra",
    description="Compras",
    category="Alimentação",
    category_id=1,
    tax_id=None,
    entry_type="texto",
    transaction_type="outcome",
    confidence=1.0,
    created_at=datetime(2025, 3, 10, 10, 0, 0),
)

MOCK_INCOME = Expense(
    id=UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"),
    amount=Decimal("3000.00"),
    date=date(2025, 3, 5),
    establishment=None,
    description="Salário",
    category="Outros",
    category_id=5,
    tax_id=None,
    entry_type="texto",
    transaction_type="income",
    confidence=1.0,
    created_at=datetime(2025, 3, 5, 9, 0, 0),
)

AUTH = {"Authorization": "Bearer valid-token"}
OUTCOME_ID = str(MOCK_OUTCOME.id)
INCOME_ID = str(MOCK_INCOME.id)


@pytest.fixture(autouse=True)
def override_auth():
    app.dependency_overrides[get_current_user] = lambda: MOCK_USER
    yield
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# TestTransactionsList — GET /api/transactions
# ---------------------------------------------------------------------------

class TestTransactionsList:
    def test_returns_paginated_results(self):
        # Arrange
        with patch("src.services.database.get_expenses_paginated", new_callable=AsyncMock) as mock_db:
            mock_db.return_value = ([MOCK_OUTCOME, MOCK_INCOME], 2)
            # Act
            response = client.get("/api/transactions", headers=AUTH)
        # Assert
        assert response.status_code == 200
        body = response.json()
        assert body["total"] == 2
        assert len(body["items"]) == 2

    def test_filter_by_outcome(self):
        # Arrange
        with patch("src.services.database.get_expenses_paginated", new_callable=AsyncMock) as mock_db:
            mock_db.return_value = ([MOCK_OUTCOME], 1)
            # Act
            response = client.get("/api/transactions?transaction_type=outcome", headers=AUTH)
            # Assert
            assert response.status_code == 200
            # Signature: get_expenses_paginated(start, end, category_id, page, page_size, transaction_type)
            # positional args: [0]=start [1]=end [2]=category_id [3]=page [4]=page_size [5]=transaction_type
            assert mock_db.call_args.args[5] == "outcome"

    def test_filter_by_income(self):
        # Arrange
        with patch("src.services.database.get_expenses_paginated", new_callable=AsyncMock) as mock_db:
            mock_db.return_value = ([MOCK_INCOME], 1)
            # Act
            response = client.get("/api/transactions?transaction_type=income", headers=AUTH)
        # Assert
        assert response.status_code == 200
        body = response.json()
        assert body["total"] == 1
        assert body["items"][0]["transaction_type"] == "income"

    def test_invalid_transaction_type_returns_422(self):
        # Arrange + Act
        response = client.get("/api/transactions?transaction_type=expense", headers=AUTH)
        # Assert
        assert response.status_code == 422

    def test_start_after_end_returns_422(self):
        # Arrange + Act
        response = client.get(
            "/api/transactions?start=2025-03-31&end=2025-03-01",
            headers=AUTH,
        )
        # Assert
        assert response.status_code == 422

    def test_page_size_capped_at_100(self):
        # Arrange
        with patch("src.services.database.get_expenses_paginated", new_callable=AsyncMock) as mock_db:
            mock_db.return_value = ([], 0)
            # Act
            response = client.get("/api/transactions?page_size=999", headers=AUTH)
        # Assert
        assert response.status_code == 200
        # Signature: (start, end, category_id, page, page_size, transaction_type)
        # args[4] = page_size — must be capped to 100
        assert mock_db.call_args.args[4] == 100

    def test_response_includes_transaction_type_field(self):
        # Arrange
        with patch("src.services.database.get_expenses_paginated", new_callable=AsyncMock) as mock_db:
            mock_db.return_value = ([MOCK_OUTCOME], 1)
            # Act
            response = client.get("/api/transactions", headers=AUTH)
        # Assert
        item = response.json()["items"][0]
        assert "transaction_type" in item
        assert item["transaction_type"] == "outcome"


# ---------------------------------------------------------------------------
# TestTransactionCreate — POST /api/transactions
# ---------------------------------------------------------------------------

class TestTransactionCreate:
    def _body(self, **overrides) -> dict:
        base = {
            "amount": 50.0,
            "date": "2025-03-10",
            "category_id": 1,
            "entry_type": "texto",
            "transaction_type": "outcome",
        }
        base.update(overrides)
        return base

    def test_create_outcome(self):
        # Arrange
        with patch("src.services.database.create_expense_direct", new_callable=AsyncMock) as mock_db:
            mock_db.return_value = MOCK_OUTCOME
            # Act
            response = client.post("/api/transactions", json=self._body(), headers=AUTH)
        # Assert
        assert response.status_code == 201
        assert response.json()["transaction_type"] == "outcome"

    def test_create_income(self):
        # Arrange
        with patch("src.services.database.create_expense_direct", new_callable=AsyncMock) as mock_db:
            mock_db.return_value = MOCK_INCOME
            # Act
            response = client.post(
                "/api/transactions",
                json=self._body(transaction_type="income", amount=3000.0),
                headers=AUTH,
            )
        # Assert
        assert response.status_code == 201
        # DB must receive transaction_type = "income"
        record = mock_db.call_args.args[0]
        assert record["transaction_type"] == "income"

    def test_missing_transaction_type_defaults_to_outcome(self):
        # Arrange: body without transaction_type — Pydantic default kicks in
        body = {
            "amount": 50.0,
            "date": "2025-03-10",
            "category_id": 1,
            "entry_type": "texto",
        }
        with patch("src.services.database.create_expense_direct", new_callable=AsyncMock) as mock_db:
            mock_db.return_value = MOCK_OUTCOME
            # Act
            response = client.post("/api/transactions", json=body, headers=AUTH)
        # Assert
        assert response.status_code == 201
        record = mock_db.call_args.args[0]
        assert record["transaction_type"] == "outcome"

    def test_invalid_transaction_type_returns_422(self):
        # Arrange + Act
        response = client.post(
            "/api/transactions",
            json=self._body(transaction_type="expense"),
            headers=AUTH,
        )
        # Assert
        assert response.status_code == 422

    def test_amount_zero_returns_422(self):
        # Arrange + Act
        response = client.post(
            "/api/transactions",
            json=self._body(amount=0),
            headers=AUTH,
        )
        # Assert
        assert response.status_code == 422

    def test_amount_negative_returns_422(self):
        # Arrange + Act
        response = client.post(
            "/api/transactions",
            json=self._body(amount=-10.0),
            headers=AUTH,
        )
        # Assert
        assert response.status_code == 422

    def test_amount_above_limit_returns_422(self):
        # Arrange + Act
        response = client.post(
            "/api/transactions",
            json=self._body(amount=1_000_000.0),
            headers=AUTH,
        )
        # Assert
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# TestTransactionUpdate — PUT /api/transactions/{id}
# ---------------------------------------------------------------------------

class TestTransactionUpdate:
    def test_update_transaction_type_to_income(self):
        # Arrange
        updated = MOCK_OUTCOME.model_copy(update={"transaction_type": "income"})
        with patch("src.services.database.update_expense", new_callable=AsyncMock) as mock_db:
            mock_db.return_value = updated
            # Act
            response = client.put(
                f"/api/transactions/{OUTCOME_ID}",
                json={"transaction_type": "income"},
                headers=AUTH,
            )
        # Assert
        assert response.status_code == 200
        assert response.json()["transaction_type"] == "income"

    def test_update_not_found_returns_404(self):
        # Arrange
        with patch("src.services.database.update_expense", new_callable=AsyncMock) as mock_db:
            mock_db.return_value = None
            # Act
            response = client.put(
                f"/api/transactions/{OUTCOME_ID}",
                json={"amount": 99.0},
                headers=AUTH,
            )
        # Assert
        assert response.status_code == 404

    def test_update_amount_invalid_returns_422(self):
        # Arrange + Act
        response = client.put(
            f"/api/transactions/{OUTCOME_ID}",
            json={"amount": -5.0},
            headers=AUTH,
        )
        # Assert
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# TestTransactionGet / Delete
# ---------------------------------------------------------------------------

class TestTransactionGetDelete:
    def test_get_existing_transaction(self):
        # Arrange
        with patch("src.services.database.get_expense_by_id", new_callable=AsyncMock) as mock_db:
            mock_db.return_value = MOCK_OUTCOME
            # Act
            response = client.get(f"/api/transactions/{OUTCOME_ID}", headers=AUTH)
        # Assert
        assert response.status_code == 200
        assert response.json()["id"] == OUTCOME_ID

    def test_get_nonexistent_returns_404(self):
        # Arrange
        with patch("src.services.database.get_expense_by_id", new_callable=AsyncMock) as mock_db:
            mock_db.return_value = None
            # Act
            response = client.get(f"/api/transactions/{OUTCOME_ID}", headers=AUTH)
        # Assert
        assert response.status_code == 404

    def test_delete_existing_returns_204(self):
        # Arrange
        with patch("src.services.database.delete_expense", new_callable=AsyncMock) as mock_db:
            mock_db.return_value = True
            # Act
            response = client.delete(f"/api/transactions/{OUTCOME_ID}", headers=AUTH)
        # Assert
        assert response.status_code == 204

    def test_delete_nonexistent_returns_404(self):
        # Arrange
        with patch("src.services.database.delete_expense", new_callable=AsyncMock) as mock_db:
            mock_db.return_value = False
            # Act
            response = client.delete(f"/api/transactions/{OUTCOME_ID}", headers=AUTH)
        # Assert
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# TestExpensesRedirect — /api/expenses → 301 → /api/transactions
# ---------------------------------------------------------------------------

class TestExpensesRedirect:
    def test_get_expenses_redirects_to_transactions(self):
        # Act
        response = client.get("/api/expenses", headers=AUTH)
        # Assert
        assert response.status_code == 301
        assert "/api/transactions" in response.headers["location"]

    def test_get_expense_by_id_redirects(self):
        # Act
        response = client.get(f"/api/expenses/{OUTCOME_ID}", headers=AUTH)
        # Assert
        assert response.status_code == 301
        assert f"/api/transactions/{OUTCOME_ID}" in response.headers["location"]

    def test_post_expenses_redirects(self):
        # Act
        response = client.post("/api/expenses", json={}, headers=AUTH)
        # Assert
        assert response.status_code == 301

    def test_delete_expense_redirects(self):
        # Act
        response = client.delete(f"/api/expenses/{OUTCOME_ID}", headers=AUTH)
        # Assert
        assert response.status_code == 301


# ---------------------------------------------------------------------------
# TestReportsSummaryFilter — GET /api/reports/summary?transaction_type=
# ---------------------------------------------------------------------------

class TestReportsSummaryFilter:
    def test_summary_without_filter_returns_all(self):
        # Arrange
        with patch("src.services.database.get_totals_by_category", new_callable=AsyncMock) as mock_db:
            mock_db.return_value = {"Alimentação": Decimal("120.00"), "Outros": Decimal("3000.00")}
            # Act
            response = client.get(
                "/api/reports/summary?start=2025-03-01&end=2025-03-31",
                headers=AUTH,
            )
        # Assert
        assert response.status_code == 200
        # Called with no transaction_type (None)
        call_kwargs = mock_db.call_args
        passed_type = call_kwargs.args[2] if len(call_kwargs.args) > 2 else call_kwargs.kwargs.get("transaction_type")
        assert passed_type is None

    def test_summary_filtered_by_outcome(self):
        # Arrange
        with patch("src.services.database.get_totals_by_category", new_callable=AsyncMock) as mock_db:
            mock_db.return_value = {"Alimentação": Decimal("120.00")}
            # Act
            response = client.get(
                "/api/reports/summary?start=2025-03-01&end=2025-03-31&transaction_type=outcome",
                headers=AUTH,
            )
        # Assert
        assert response.status_code == 200
        call_kwargs = mock_db.call_args
        passed_type = call_kwargs.args[2] if len(call_kwargs.args) > 2 else call_kwargs.kwargs.get("transaction_type")
        assert passed_type == "outcome"

    def test_summary_filtered_by_income(self):
        # Arrange
        with patch("src.services.database.get_totals_by_category", new_callable=AsyncMock) as mock_db:
            mock_db.return_value = {"Outros": Decimal("3000.00")}
            # Act
            response = client.get(
                "/api/reports/summary?start=2025-03-01&end=2025-03-31&transaction_type=income",
                headers=AUTH,
            )
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data[0]["category"] == "Outros"

    def test_summary_invalid_transaction_type_returns_422(self):
        # Arrange + Act
        response = client.get(
            "/api/reports/summary?start=2025-03-01&end=2025-03-31&transaction_type=invalid",
            headers=AUTH,
        )
        # Assert
        assert response.status_code == 422

    def test_summary_results_ordered_by_total_desc(self):
        # Arrange
        with patch("src.services.database.get_totals_by_category", new_callable=AsyncMock) as mock_db:
            mock_db.return_value = {
                "Lazer": Decimal("50.00"),
                "Alimentação": Decimal("200.00"),
                "Transporte": Decimal("100.00"),
            }
            # Act
            response = client.get(
                "/api/reports/summary?start=2025-03-01&end=2025-03-31",
                headers=AUTH,
            )
        # Assert
        totals = [float(item["total"]) for item in response.json()]
        assert totals == sorted(totals, reverse=True)
