import pytest
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import AsyncMock

from src.agents.reporter import generate_report, _fmt


def _expense(categoria: str, valor: str, estabelecimento: str | None = None) -> object:
    from src.models.expense import Expense
    return Expense(
        id="550e8400-e29b-41d4-a716-446655440001",
        valor=Decimal(valor),
        data=date(2024, 1, 15),
        estabelecimento=estabelecimento,
        descricao=None,
        categoria=categoria,
        cnpj=None,
        tipo_entrada="texto",
        confianca=0.9,
        created_at=datetime(2024, 1, 15, 10, 0, 0),
    )


START = date(2024, 1, 1)
END = date(2024, 1, 31)


@pytest.fixture
def mock_insight(mocker):
    mocker.patch(
        "src.agents.reporter.llm.chat_completion",
        new_callable=AsyncMock,
        return_value="Seus gastos com alimentação estão acima da média.",
    )


class TestGenerateReport:
    @pytest.mark.asyncio
    async def test_empty_period_returns_friendly_message(self, mocker):
        mocker.patch("src.services.database.get_expenses_by_period", new_callable=AsyncMock, return_value=[])

        result = await generate_report(START, END)

        assert "Nenhuma despesa" in result
        assert "01/01/2024" in result

    @pytest.mark.asyncio
    async def test_report_contains_total(self, mock_insight, mocker):
        expenses = [
            _expense("Alimentação", "100.00", "Mercado"),
            _expense("Transporte", "50.00"),
        ]
        mocker.patch("src.services.database.get_expenses_by_period", new_callable=AsyncMock, return_value=expenses)

        result = await generate_report(START, END)

        assert "150,00" in result

    @pytest.mark.asyncio
    async def test_report_contains_categories(self, mock_insight, mocker):
        expenses = [
            _expense("Alimentação", "200.00"),
            _expense("Saúde", "80.00"),
        ]
        mocker.patch("src.services.database.get_expenses_by_period", new_callable=AsyncMock, return_value=expenses)

        result = await generate_report(START, END)

        assert "Alimentação" in result
        assert "Saúde" in result

    @pytest.mark.asyncio
    async def test_report_contains_percentages(self, mock_insight, mocker):
        expenses = [
            _expense("Alimentação", "300.00"),
            _expense("Transporte", "100.00"),
        ]
        mocker.patch("src.services.database.get_expenses_by_period", new_callable=AsyncMock, return_value=expenses)

        result = await generate_report(START, END)

        assert "75%" in result   # 300/400
        assert "25%" in result   # 100/400

    @pytest.mark.asyncio
    async def test_report_contains_insight(self, mock_insight, mocker):
        expenses = [_expense("Alimentação", "100.00")]
        mocker.patch("src.services.database.get_expenses_by_period", new_callable=AsyncMock, return_value=expenses)

        result = await generate_report(START, END)

        assert "Seus gastos com alimentação estão acima da média." in result

    @pytest.mark.asyncio
    async def test_llm_failure_still_returns_report(self, mocker):
        expenses = [_expense("Alimentação", "100.00")]
        mocker.patch("src.services.database.get_expenses_by_period", new_callable=AsyncMock, return_value=expenses)
        mocker.patch(
            "src.agents.reporter.llm.chat_completion",
            new_callable=AsyncMock,
            side_effect=Exception("LLM timeout"),
        )

        result = await generate_report(START, END)

        assert "100,00" in result
        assert "Não foi possível gerar o insight" in result

    @pytest.mark.asyncio
    async def test_semana_label_in_report(self, mock_insight, mocker):
        expenses = [_expense("Lazer", "50.00")]
        mocker.patch("src.services.database.get_expenses_by_period", new_callable=AsyncMock, return_value=expenses)

        start = date(2024, 1, 24)
        end = date(2024, 1, 31)
        result = await generate_report(start, end)

        assert "Últimos 7 dias" in result

    @pytest.mark.asyncio
    async def test_top_establishments_shown(self, mock_insight, mocker):
        expenses = [
            _expense("Alimentação", "50.00", "iFood"),
            _expense("Alimentação", "60.00", "iFood"),
            _expense("Transporte", "30.00", "99"),
        ]
        mocker.patch("src.services.database.get_expenses_by_period", new_callable=AsyncMock, return_value=expenses)

        result = await generate_report(START, END)

        assert "iFood" in result


class TestFmt:
    def test_formats_decimal_with_comma(self):
        assert _fmt(Decimal("1234.50")) == "1.234,50"

    def test_formats_small_value(self):
        assert _fmt(Decimal("45.90")) == "45,90"
