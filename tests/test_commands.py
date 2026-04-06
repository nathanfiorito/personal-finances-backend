import pytest
from datetime import date, timedelta
from unittest.mock import AsyncMock, patch

from src.handlers.commands import dispatch_command, handle_relatorio


CHAT_ID = 12345


@pytest.fixture(autouse=True)
def mock_telegram(mocker):
    mocker.patch("src.handlers.commands.telegram.send_message", new_callable=AsyncMock)


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
        assert "desconhecido" in mock_send.call_args[0][1].lower() or \
               "/desconhecido" in mock_send.call_args[0][1]

    @pytest.mark.asyncio
    async def test_botname_suffix_stripped(self, mocker):
        mock_start = mocker.patch("src.handlers.commands.handle_start", new_callable=AsyncMock)
        await dispatch_command(CHAT_ID, "/start@FinBot")
        mock_start.assert_called_once_with(CHAT_ID)


class TestHandleRelatorio:
    @pytest.mark.asyncio
    async def test_semana_uses_last_7_days(self, mocker):
        mock_generate = mocker.patch("src.agents.reporter.generate_report", new_callable=AsyncMock, return_value="relatório")
        await handle_relatorio(CHAT_ID, ["semana"])

        start, end = mock_generate.call_args[0]
        assert (end - start).days == 7

    @pytest.mark.asyncio
    async def test_mes_starts_on_first_of_month(self, mocker):
        mock_generate = mocker.patch("src.agents.reporter.generate_report", new_callable=AsyncMock, return_value="relatório")
        await handle_relatorio(CHAT_ID, ["mes"])

        start, end = mock_generate.call_args[0]
        assert start.day == 1
        assert end == date.today()

    @pytest.mark.asyncio
    async def test_default_is_mes(self, mocker):
        mock_generate = mocker.patch("src.agents.reporter.generate_report", new_callable=AsyncMock, return_value="relatório")
        await handle_relatorio(CHAT_ID, [])

        start, end = mock_generate.call_args[0]
        assert start.day == 1

    @pytest.mark.asyncio
    async def test_sends_report_message(self, mocker):
        mocker.patch("src.agents.reporter.generate_report", new_callable=AsyncMock, return_value="📊 Relatório aqui")
        mock_send = mocker.patch("src.handlers.commands.telegram.send_message", new_callable=AsyncMock)

        await handle_relatorio(CHAT_ID, ["mes"])

        # Second call should be the report (first is "⏳ Gerando...")
        assert mock_send.call_count == 2
        assert "📊 Relatório aqui" in mock_send.call_args[0][1]
