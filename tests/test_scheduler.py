import pytest
from datetime import date
from unittest.mock import AsyncMock, patch

from src.scheduler.reports import send_monthly_report


class TestSendMonthlyReport:
    @pytest.mark.asyncio
    async def test_calls_generate_report_with_previous_month(self, mocker):
        mock_generate = mocker.patch("src.agents.reporter.generate_report", new_callable=AsyncMock, return_value="relatório")
        mocker.patch("src.services.telegram.send_message", new_callable=AsyncMock)

        # Freeze "today" to 2024-03-01 so previous month is February 2024
        with patch("src.scheduler.reports.date") as mock_date:
            mock_date.today.return_value = date(2024, 3, 1)
            mock_date.side_effect = lambda *a, **kw: date(*a, **kw)
            await send_monthly_report()

        start, end = mock_generate.call_args[0]
        assert start == date(2024, 2, 1)
        assert end == date(2024, 2, 29)  # 2024 is a leap year

    @pytest.mark.asyncio
    async def test_january_wraps_to_december_of_previous_year(self, mocker):
        mock_generate = mocker.patch("src.agents.reporter.generate_report", new_callable=AsyncMock, return_value="relatório")
        mocker.patch("src.services.telegram.send_message", new_callable=AsyncMock)

        with patch("src.scheduler.reports.date") as mock_date:
            mock_date.today.return_value = date(2024, 1, 1)
            mock_date.side_effect = lambda *a, **kw: date(*a, **kw)
            await send_monthly_report()

        start, end = mock_generate.call_args[0]
        assert start == date(2023, 12, 1)
        assert end == date(2023, 12, 31)

    @pytest.mark.asyncio
    async def test_sends_to_allowed_chat_id(self, mocker):
        mocker.patch("src.agents.reporter.generate_report", new_callable=AsyncMock, return_value="relatório")
        mock_send = mocker.patch("src.services.telegram.send_message", new_callable=AsyncMock)

        from src.config.settings import settings
        await send_monthly_report()

        assert mock_send.call_args[0][0] == settings.telegram_allowed_chat_id

    @pytest.mark.asyncio
    async def test_exception_does_not_propagate(self, mocker):
        mocker.patch("src.agents.reporter.generate_report", new_callable=AsyncMock, side_effect=Exception("DB down"))

        # Should not raise
        await send_monthly_report()
