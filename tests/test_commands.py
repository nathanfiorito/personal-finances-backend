import pytest
from datetime import date, timedelta
from unittest.mock import AsyncMock, patch

from src.handlers.commands import dispatch_command, handle_relatorio, _parse_periodo


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
        await dispatch_command(CHAT_ID, "/start@FinBot")
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
