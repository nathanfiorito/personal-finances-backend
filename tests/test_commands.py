import pytest
from datetime import date, timedelta
from unittest.mock import AsyncMock, patch

from src.handlers.commands import dispatch_command, handle_relatorio, handle_exportar, handle_categorias, _parse_periodo, _generate_csv, _handle_categorias_add


CHAT_ID = 12345


@pytest.fixture(autouse=True)
def mock_telegram(mocker):
    mocker.patch("src.handlers.commands.telegram.send_message", new_callable=AsyncMock)


class TestParsePeriodo:
    TODAY = date(2025, 4, 6)

    def test_empty_args_returns_current_month(self):
        start, end = _parse_periodo([], self.TODAY)
        assert start == date(2025, 4, 1)
        assert end == self.TODAY

    def test_mes_returns_current_month(self):
        start, end = _parse_periodo(["mes"], self.TODAY)
        assert start == date(2025, 4, 1)
        assert end == self.TODAY

    def test_semana_returns_last_7_days(self):
        start, end = _parse_periodo(["semana"], self.TODAY)
        assert (end - start).days == 7
        assert end == self.TODAY

    def test_anterior_returns_previous_month(self):
        start, end = _parse_periodo(["anterior"], self.TODAY)
        assert start == date(2025, 3, 1)
        assert end == date(2025, 3, 31)

    def test_anterior_in_january_wraps_to_december(self):
        start, end = _parse_periodo(["anterior"], date(2025, 1, 15))
        assert start == date(2024, 12, 1)
        assert end == date(2024, 12, 31)

    def test_mm_aaaa_past_month(self):
        start, end = _parse_periodo(["03/2025"], self.TODAY)
        assert start == date(2025, 3, 1)
        assert end == date(2025, 3, 31)

    def test_mm_aaaa_current_month_caps_at_today(self):
        start, end = _parse_periodo(["04/2025"], self.TODAY)
        assert start == date(2025, 4, 1)
        assert end == self.TODAY

    def test_mm_aaaa_february_leap_year(self):
        start, end = _parse_periodo(["02/2024"], self.TODAY)
        assert end == date(2024, 2, 29)

    def test_mm_aaaa_february_non_leap_year(self):
        start, end = _parse_periodo(["02/2025"], self.TODAY)
        assert end == date(2025, 2, 28)

    def test_invalid_month_returns_none(self):
        assert _parse_periodo(["13/2025"], self.TODAY) is None

    def test_invalid_format_returns_none(self):
        assert _parse_periodo(["março"], self.TODAY) is None

    def test_invalid_year_returns_none(self):
        assert _parse_periodo(["01/1999"], self.TODAY) is None


class TestDispatchCommand:
    @pytest.mark.asyncio
    async def test_start_command(self, mocker):
        mock_start = mocker.patch("src.handlers.commands.handle_start", new_callable=AsyncMock)
        await dispatch_command(CHAT_ID, "/start")
        mock_start.assert_called_once_with(CHAT_ID)

    @pytest.mark.asyncio
    async def test_ajuda_command(self, mocker):
        mock_ajuda = mocker.patch("src.handlers.commands.handle_ajuda", new_callable=AsyncMock)
        await dispatch_command(CHAT_ID, "/ajuda")
        mock_ajuda.assert_called_once_with(CHAT_ID)

    @pytest.mark.asyncio
    async def test_relatorio_command_passes_args(self, mocker):
        mock_rel = mocker.patch("src.handlers.commands.handle_relatorio", new_callable=AsyncMock)
        await dispatch_command(CHAT_ID, "/relatorio semana")
        mock_rel.assert_called_once_with(CHAT_ID, ["semana"])

    @pytest.mark.asyncio
    async def test_relatorio_no_args(self, mocker):
        mock_rel = mocker.patch("src.handlers.commands.handle_relatorio", new_callable=AsyncMock)
        await dispatch_command(CHAT_ID, "/relatorio")
        mock_rel.assert_called_once_with(CHAT_ID, [])

    @pytest.mark.asyncio
    async def test_unknown_command(self, mocker):
        mock_send = mocker.patch("src.handlers.commands.telegram.send_message", new_callable=AsyncMock)
        await dispatch_command(CHAT_ID, "/desconhecido")
        assert "/desconhecido" in mock_send.call_args[0][1]

    @pytest.mark.asyncio
    async def test_botname_suffix_stripped(self, mocker):
        mock_start = mocker.patch("src.handlers.commands.handle_start", new_callable=AsyncMock)
        await dispatch_command(CHAT_ID, "/start@PersonalFinancesBot")
        mock_start.assert_called_once_with(CHAT_ID)


class TestHandleRelatorio:
    @pytest.mark.asyncio
    async def test_semana_calls_generate_with_7_days(self, mocker):
        mock_generate = mocker.patch("src.agents.reporter.generate_report", new_callable=AsyncMock, return_value="relatório")
        await handle_relatorio(CHAT_ID, ["semana"])
        start, end = mock_generate.call_args[0]
        assert (end - start).days == 7

    @pytest.mark.asyncio
    async def test_mes_starts_on_first(self, mocker):
        mock_generate = mocker.patch("src.agents.reporter.generate_report", new_callable=AsyncMock, return_value="relatório")
        await handle_relatorio(CHAT_ID, ["mes"])
        start, end = mock_generate.call_args[0]
        assert start.day == 1
        assert end == date.today()

    @pytest.mark.asyncio
    async def test_anterior_calls_previous_month(self, mocker):
        mock_generate = mocker.patch("src.agents.reporter.generate_report", new_callable=AsyncMock, return_value="relatório")
        await handle_relatorio(CHAT_ID, ["anterior"])
        start, end = mock_generate.call_args[0]
        today = date.today()
        expected_month = today.month - 1 if today.month > 1 else 12
        assert start.day == 1
        assert start.month == expected_month
        assert end.month == expected_month

    @pytest.mark.asyncio
    async def test_mm_aaaa_calls_correct_period(self, mocker):
        mock_generate = mocker.patch("src.agents.reporter.generate_report", new_callable=AsyncMock, return_value="relatório")
        await handle_relatorio(CHAT_ID, ["01/2025"])
        start, end = mock_generate.call_args[0]
        assert start == date(2025, 1, 1)
        assert end == date(2025, 1, 31)

    @pytest.mark.asyncio
    async def test_invalid_period_sends_error(self, mocker):
        mock_generate = mocker.patch("src.agents.reporter.generate_report", new_callable=AsyncMock)
        mock_send = mocker.patch("src.handlers.commands.telegram.send_message", new_callable=AsyncMock)
        await handle_relatorio(CHAT_ID, ["13/2025"])
        mock_generate.assert_not_called()
        assert "inválido" in mock_send.call_args[0][1].lower()

    @pytest.mark.asyncio
    async def test_default_is_current_month(self, mocker):
        mock_generate = mocker.patch("src.agents.reporter.generate_report", new_callable=AsyncMock, return_value="relatório")
        await handle_relatorio(CHAT_ID, [])
        start, end = mock_generate.call_args[0]
        assert start.day == 1

    @pytest.mark.asyncio
    async def test_sends_report_message(self, mocker):
        mocker.patch("src.agents.reporter.generate_report", new_callable=AsyncMock, return_value="📊 Relatório aqui")
        mock_send = mocker.patch("src.handlers.commands.telegram.send_message", new_callable=AsyncMock)
        await handle_relatorio(CHAT_ID, ["mes"])
        assert mock_send.call_count == 2
        assert "📊 Relatório aqui" in mock_send.call_args[0][1]


class TestHandleExportar:
    @pytest.mark.asyncio
    async def test_sends_csv_document(self, mocker):
        from datetime import datetime
        from decimal import Decimal
        from src.models.expense import Expense
        expense = Expense(
            id="550e8400-e29b-41d4-a716-446655440001",
            amount=Decimal("50.00"), date=date(2025, 3, 10),
            establishment="Mercado", description=None, category="Alimentação",
            tax_id=None, entry_type="texto", confidence=0.9,
            created_at=datetime(2025, 3, 10, 10, 0, 0),
        )
        mocker.patch("src.services.database.get_expenses_by_period", new_callable=AsyncMock, return_value=[expense])
        mock_doc = mocker.patch("src.services.telegram.send_document", new_callable=AsyncMock)
        mocker.patch("src.handlers.commands.telegram.send_message", new_callable=AsyncMock)

        await handle_exportar(CHAT_ID, ["03/2025"])

        mock_doc.assert_called_once()
        filename = mock_doc.call_args[0][2]
        assert filename.endswith(".csv")
        assert "03-2025" in filename

    @pytest.mark.asyncio
    async def test_empty_period_sends_message(self, mocker):
        mocker.patch("src.services.database.get_expenses_by_period", new_callable=AsyncMock, return_value=[])
        mock_send = mocker.patch("src.handlers.commands.telegram.send_message", new_callable=AsyncMock)

        await handle_exportar(CHAT_ID, ["03/2025"])

        mock_send.assert_called()
        assert "Nenhuma" in mock_send.call_args[0][1]

    @pytest.mark.asyncio
    async def test_invalid_period_sends_error(self, mocker):
        mock_db = mocker.patch("src.services.database.get_expenses_by_period", new_callable=AsyncMock)
        mock_send = mocker.patch("src.handlers.commands.telegram.send_message", new_callable=AsyncMock)

        await handle_exportar(CHAT_ID, ["13/2025"])

        mock_db.assert_not_called()
        assert "inválido" in mock_send.call_args[0][1].lower()


class TestGenerateCsv:
    def test_csv_has_bom(self):
        from datetime import datetime
        from decimal import Decimal
        from src.models.expense import Expense
        expense = Expense(
            id="550e8400-e29b-41d4-a716-446655440001",
            amount=Decimal("45.90"), date=date(2025, 1, 15),
            establishment="Mercado", description="Compras", category="Alimentação",
            tax_id=None, entry_type="texto", confidence=0.9,
            created_at=datetime(2025, 1, 15, 10, 0, 0),
        )
        result = _generate_csv([expense])
        assert result.startswith(b"\xef\xbb\xbf")

    def test_csv_contains_expense_data(self):
        from datetime import datetime
        from decimal import Decimal
        from src.models.expense import Expense
        expense = Expense(
            id="550e8400-e29b-41d4-a716-446655440001",
            amount=Decimal("45.90"), date=date(2025, 1, 15),
            establishment="Mercado", description="Compras", category="Alimentação",
            tax_id=None, entry_type="texto", confidence=0.9,
            created_at=datetime(2025, 1, 15, 10, 0, 0),
        )
        result = _generate_csv([expense]).decode("utf-8-sig")
        assert "Mercado" in result
        assert "Alimentação" in result
        assert "45,90" in result


class TestHandleCategorias:
    @pytest.mark.asyncio
    async def test_lists_categories_from_db(self, mocker):
        mocker.patch(
            "src.services.database.get_active_categories",
            new_callable=AsyncMock,
            return_value=["Alimentação", "Saúde", "Transporte"],
        )
        mock_send = mocker.patch("src.handlers.commands.telegram.send_message", new_callable=AsyncMock)

        await handle_categorias(CHAT_ID, [])

        text = mock_send.call_args[0][1]
        assert "Alimentação" in text
        assert "Saúde" in text

    @pytest.mark.asyncio
    async def test_falls_back_to_default_on_db_error(self, mocker):
        mocker.patch(
            "src.services.database.get_active_categories",
            new_callable=AsyncMock,
            side_effect=Exception("DB error"),
        )
        mock_send = mocker.patch("src.handlers.commands.telegram.send_message", new_callable=AsyncMock)

        await handle_categorias(CHAT_ID, [])

        text = mock_send.call_args[0][1]
        assert "Outros" in text

    @pytest.mark.asyncio
    async def test_shows_add_hint(self, mocker):
        mocker.patch("src.services.database.get_active_categories", new_callable=AsyncMock, return_value=["Alimentação"])
        mock_send = mocker.patch("src.handlers.commands.telegram.send_message", new_callable=AsyncMock)

        await handle_categorias(CHAT_ID, [])

        assert "add" in mock_send.call_args[0][1].lower()


class TestHandleCategoriasAdd:
    @pytest.mark.asyncio
    async def test_adds_category_successfully(self, mocker):
        mock_add = mocker.patch("src.services.database.add_category", new_callable=AsyncMock)
        mocker.patch("src.agents.categorizer.invalidate_cache")
        mock_send = mocker.patch("src.handlers.commands.telegram.send_message", new_callable=AsyncMock)

        await _handle_categorias_add(CHAT_ID, ["Investimentos"])

        mock_add.assert_called_once_with("Investimentos")
        assert "Investimentos" in mock_send.call_args[0][1]
        assert "✅" in mock_send.call_args[0][1]

    @pytest.mark.asyncio
    async def test_invalidates_cache_after_add(self, mocker):
        mocker.patch("src.services.database.add_category", new_callable=AsyncMock)
        mock_invalidate = mocker.patch("src.agents.categorizer.invalidate_cache")
        mocker.patch("src.handlers.commands.telegram.send_message", new_callable=AsyncMock)

        await _handle_categorias_add(CHAT_ID, ["Investimentos"])

        mock_invalidate.assert_called_once()

    @pytest.mark.asyncio
    async def test_empty_name_shows_usage(self, mocker):
        mock_add = mocker.patch("src.services.database.add_category", new_callable=AsyncMock)
        mock_send = mocker.patch("src.handlers.commands.telegram.send_message", new_callable=AsyncMock)

        await _handle_categorias_add(CHAT_ID, [])

        mock_add.assert_not_called()
        assert "Informe" in mock_send.call_args[0][1]

    @pytest.mark.asyncio
    async def test_duplicate_category_shows_warning(self, mocker):
        mocker.patch(
            "src.services.database.add_category",
            new_callable=AsyncMock,
            side_effect=Exception("duplicate key value violates unique constraint"),
        )
        mock_send = mocker.patch("src.handlers.commands.telegram.send_message", new_callable=AsyncMock)

        await _handle_categorias_add(CHAT_ID, ["Alimentação"])

        assert "já existe" in mock_send.call_args[0][1]

    @pytest.mark.asyncio
    async def test_multi_word_category_name(self, mocker):
        mock_add = mocker.patch("src.services.database.add_category", new_callable=AsyncMock)
        mocker.patch("src.agents.categorizer.invalidate_cache")
        mocker.patch("src.handlers.commands.telegram.send_message", new_callable=AsyncMock)

        await _handle_categorias_add(CHAT_ID, ["Assinaturas", "Digitais"])

        mock_add.assert_called_once_with("Assinaturas Digitais")
