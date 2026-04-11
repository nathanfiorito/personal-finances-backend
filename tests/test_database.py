import pytest
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import src.services.database as db_module
from src.models.expense import Expense, ExtractedExpense


def _expense() -> ExtractedExpense:
    return ExtractedExpense(
        amount=Decimal("45.90"),
        date=date(2024, 1, 15),
        establishment="Supermercado Extra",
        description="Compras do mês",
        entry_type="texto",
        confidence=0.9,
    )


def _expense_row(id_: str = "550e8400-e29b-41d4-a716-446655440000", category: str = "Alimentação") -> dict:
    return {
        "id": id_,
        "amount": "45.90",
        "date": "2024-01-15",
        "establishment": "Supermercado Extra",
        "description": "Compras do mês",
        "category_id": 1,
        "categories": {"name": category},
        "tax_id": None,
        "entry_type": "texto",
        "confidence": 0.9,
        "created_at": "2024-01-15T10:00:00+00:00",
    }


def _make_saved_expense(**kwargs) -> Expense:
    defaults = dict(
        id="550e8400-e29b-41d4-a716-446655440000",
        amount=Decimal("45.90"),
        date=date(2024, 1, 15),
        establishment="Supermercado Extra",
        description="Compras do mês",
        category="Alimentação",
        tax_id=None,
        entry_type="texto",
        confidence=0.9,
        created_at=datetime(2024, 1, 15, 10, 0, 0),
    )
    defaults.update(kwargs)
    return Expense(**defaults)


@pytest.fixture(autouse=True)
def reset_client():
    original = db_module._client
    db_module._client = None
    yield
    db_module._client = original


def _mock_supabase() -> MagicMock:
    mock = MagicMock()
    # insert chain
    mock.table.return_value.insert.return_value.execute = AsyncMock()
    # category id lookup: .select().eq().limit().execute()
    mock.table.return_value.select.return_value \
        .eq.return_value \
        .limit.return_value \
        .execute = AsyncMock(return_value=MagicMock(data=[{"id": 1}]))
    # expenses select chain: .select().gte().lte().order().execute()
    mock.table.return_value.select.return_value \
        .gte.return_value \
        .lte.return_value \
        .order.return_value \
        .execute = AsyncMock()
    return mock


# --- save_expense ---

class TestSaveExpense:
    @pytest.mark.asyncio
    async def test_returns_uuid_on_success(self, mocker):
        mock_client = _mock_supabase()
        expected_id = "550e8400-e29b-41d4-a716-446655440000"
        mock_client.table.return_value.insert.return_value.execute.return_value.data = [
            {"id": expected_id}
        ]
        mock_get = mocker.patch("src.services.database._get_client", new_callable=AsyncMock)
        mock_get.return_value = mock_client

        result = await db_module.save_expense(_expense(), "Alimentação")

        assert result == expected_id

    @pytest.mark.asyncio
    async def test_sends_correct_fields(self, mocker):
        mock_client = _mock_supabase()
        mock_client.table.return_value.insert.return_value.execute.return_value.data = [
            {"id": "uuid-1"}
        ]
        mock_get = mocker.patch("src.services.database._get_client", new_callable=AsyncMock)
        mock_get.return_value = mock_client

        await db_module.save_expense(_expense(), "Alimentação")

        inserted = mock_client.table.return_value.insert.call_args[0][0]
        assert inserted["amount"] == "45.90"
        assert inserted["date"] == "2024-01-15"
        assert inserted["category_id"] == 1
        assert inserted["entry_type"] == "texto"
        assert inserted["confidence"] == 0.9
        assert inserted["establishment"] == "Supermercado Extra"

    @pytest.mark.asyncio
    async def test_propagates_db_exception(self, mocker):
        mock_client = _mock_supabase()
        mock_client.table.return_value.insert.return_value.execute.side_effect = Exception("connection failed")
        mock_get = mocker.patch("src.services.database._get_client", new_callable=AsyncMock)
        mock_get.return_value = mock_client

        with pytest.raises(Exception, match="connection failed"):
            await db_module.save_expense(_expense(), "Alimentação")


# --- get_expenses_by_period ---

class TestGetExpensesByPeriod:
    @pytest.mark.asyncio
    async def test_returns_list_of_expenses(self, mocker):
        mock_client = _mock_supabase()
        mock_client.table.return_value.select.return_value \
            .gte.return_value.lte.return_value.order.return_value \
            .execute.return_value.data = [_expense_row()]
        mock_get = mocker.patch("src.services.database._get_client", new_callable=AsyncMock)
        mock_get.return_value = mock_client

        result = await db_module.get_expenses_by_period(date(2024, 1, 1), date(2024, 1, 31))

        assert len(result) == 1
        assert isinstance(result[0], Expense)
        assert result[0].amount == Decimal("45.90")
        assert result[0].category == "Alimentação"

    @pytest.mark.asyncio
    async def test_passes_correct_date_filters(self, mocker):
        mock_client = _mock_supabase()
        mock_client.table.return_value.select.return_value \
            .gte.return_value.lte.return_value.order.return_value \
            .execute.return_value.data = []
        mock_get = mocker.patch("src.services.database._get_client", new_callable=AsyncMock)
        mock_get.return_value = mock_client

        await db_module.get_expenses_by_period(date(2024, 1, 1), date(2024, 1, 31))

        select_chain = mock_client.table.return_value.select.return_value
        select_chain.gte.assert_called_once_with("date", "2024-01-01")
        select_chain.gte.return_value.lte.assert_called_once_with("date", "2024-01-31")

    @pytest.mark.asyncio
    async def test_empty_period_returns_empty_list(self, mocker):
        mock_client = _mock_supabase()
        mock_client.table.return_value.select.return_value \
            .gte.return_value.lte.return_value.order.return_value \
            .execute.return_value.data = []
        mock_get = mocker.patch("src.services.database._get_client", new_callable=AsyncMock)
        mock_get.return_value = mock_client

        result = await db_module.get_expenses_by_period(date(2024, 2, 1), date(2024, 2, 28))

        assert result == []


# --- get_totals_by_category ---

class TestGetTotalsByCategory:
    @pytest.mark.asyncio
    async def test_aggregates_by_category(self, mocker):
        expenses = [
            _make_saved_expense(id_="u1", amount=Decimal("50.00"), category="Alimentação"),
            _make_saved_expense(id_="u2", amount=Decimal("30.00"), category="Alimentação"),
            _make_saved_expense(id_="u3", amount=Decimal("100.00"), category="Transporte"),
        ]
        mocker.patch("src.services.database.get_expenses_by_period", return_value=expenses)

        result = await db_module.get_totals_by_category(date(2024, 1, 1), date(2024, 1, 31))

        assert result["Alimentação"] == Decimal("80.00")
        assert result["Transporte"] == Decimal("100.00")

    @pytest.mark.asyncio
    async def test_empty_returns_empty_dict(self, mocker):
        mocker.patch("src.services.database.get_expenses_by_period", return_value=[])

        result = await db_module.get_totals_by_category(date(2024, 1, 1), date(2024, 1, 31))

        assert result == {}

    @pytest.mark.asyncio
    async def test_single_category(self, mocker):
        expenses = [
            _make_saved_expense(id_="u1", amount=Decimal("25.00"), category="Saúde"),
            _make_saved_expense(id_="u2", amount=Decimal("75.50"), category="Saúde"),
        ]
        mocker.patch("src.services.database.get_expenses_by_period", return_value=expenses)

        result = await db_module.get_totals_by_category(date(2024, 1, 1), date(2024, 1, 31))

        assert len(result) == 1
        assert result["Saúde"] == Decimal("100.50")


class TestTimedDb:
    @pytest.mark.asyncio
    async def test_yields_span_with_set_attribute(self):
        """_timed_db must yield an object whose set_attribute is callable."""
        async with db_module._timed_db("transactions.select(*)") as span:
            span.set_attribute("db.rows", 7)  # must not raise

    @pytest.mark.asyncio
    async def test_propagates_exception_and_reraises(self):
        with pytest.raises(RuntimeError, match="db exploded"):
            async with db_module._timed_db("transactions.select(*)"):
                raise RuntimeError("db exploded")

    @pytest.mark.asyncio
    async def test_exception_records_on_span(self, mocker):
        mock_span = MagicMock()
        mock_ctx = MagicMock()
        mock_ctx.__enter__.return_value = mock_span
        mock_ctx.__exit__.return_value = False
        mocker.patch("src.services.database.tracing.start_span", return_value=mock_ctx)

        with pytest.raises(RuntimeError, match="db exploded"):
            async with db_module._timed_db("transactions.select(*)"):
                raise RuntimeError("db exploded")

        mock_span.record_exception.assert_called_once()
        mock_span.set_status.assert_called_once()


class TestDbSpanAttrs:
    def test_select_with_period(self):
        result = db_module._db_span_attrs("transactions.select(*).period(2024-01-01,2024-01-31)")
        assert result == {"db.table": "transactions", "db.operation": "select"}

    def test_insert(self):
        result = db_module._db_span_attrs("transactions.insert")
        assert result == {"db.table": "transactions", "db.operation": "insert"}

    def test_update_with_args(self):
        result = db_module._db_span_attrs("categories.update(is_active=False).eq(id=5)")
        assert result == {"db.table": "categories", "db.operation": "update"}

    def test_no_dot_falls_back_to_query(self):
        result = db_module._db_span_attrs("unknown_operation")
        assert result == {"db.table": "unknown_operation", "db.operation": "query"}
