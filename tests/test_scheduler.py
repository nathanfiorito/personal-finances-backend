from datetime import date
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from src.scheduler.reports import send_monthly_report
import src.scheduler.reports as scheduler_module


def _make_use_cases(report_mock=None):
    """Build a stub use_cases with a generate_telegram_report that calls report_mock."""
    if report_mock is None:
        report_mock = AsyncMock()
    uc = SimpleNamespace(generate_telegram_report=SimpleNamespace(execute=report_mock))
    return uc, report_mock


class TestSendMonthlyReport:
    @pytest.fixture(autouse=True)
    def wire_use_cases(self):
        """Ensure _use_cases is always reset after each test."""
        yield
        scheduler_module._use_cases = None

    @pytest.mark.asyncio
    async def test_calls_generate_report_with_previous_month(self):
        uc, mock_execute = _make_use_cases()
        scheduler_module._use_cases = uc

        with patch("src.scheduler.reports.date") as mock_date:
            mock_date.today.return_value = date(2024, 3, 1)
            mock_date.side_effect = lambda *a, **kw: date(*a, **kw)
            await send_monthly_report()

        mock_execute.assert_called_once()
        cmd = mock_execute.call_args[0][0]
        assert cmd.start == date(2024, 2, 1)
        assert cmd.end == date(2024, 2, 29)  # 2024 is a leap year

    @pytest.mark.asyncio
    async def test_january_wraps_to_december_of_previous_year(self):
        uc, mock_execute = _make_use_cases()
        scheduler_module._use_cases = uc

        with patch("src.scheduler.reports.date") as mock_date:
            mock_date.today.return_value = date(2024, 1, 1)
            mock_date.side_effect = lambda *a, **kw: date(*a, **kw)
            await send_monthly_report()

        cmd = mock_execute.call_args[0][0]
        assert cmd.start == date(2023, 12, 1)
        assert cmd.end == date(2023, 12, 31)

    @pytest.mark.asyncio
    async def test_sends_to_allowed_chat_id(self):
        from src.config.settings import settings
        uc, mock_execute = _make_use_cases()
        scheduler_module._use_cases = uc

        await send_monthly_report()

        cmd = mock_execute.call_args[0][0]
        assert cmd.chat_id == settings.telegram_allowed_chat_id

    @pytest.mark.asyncio
    async def test_exception_does_not_propagate(self):
        uc, mock_execute = _make_use_cases(AsyncMock(side_effect=Exception("DB down")))
        scheduler_module._use_cases = uc

        # Should not raise
        await send_monthly_report()

    @pytest.mark.asyncio
    async def test_no_use_cases_logs_and_returns(self):
        scheduler_module._use_cases = None
        # Should not raise even with no use_cases wired
        await send_monthly_report()
