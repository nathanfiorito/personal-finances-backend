import calendar
import logging
from datetime import date

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from src.config.settings import settings

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler(timezone="America/Sao_Paulo")

# Set at startup via start_scheduler(use_cases=...) — avoids circular imports.
_use_cases = None


async def send_monthly_report() -> None:
    """Sends the previous month's report. Called automatically on the 1st of each month."""
    if _use_cases is None:
        logger.error("send_monthly_report: use_cases not wired — skipping")
        return
    try:
        today = date.today()
        if today.month == 1:
            year, month = today.year - 1, 12
        else:
            year, month = today.year, today.month - 1

        start = date(year, month, 1)
        end = date(year, month, calendar.monthrange(year, month)[1])
        label = start.strftime("%B %Y").capitalize()

        from src.v2.domain.use_cases.telegram.generate_telegram_report import (
            GenerateTelegramReportCommand,
        )
        await _use_cases.generate_telegram_report.execute(
            GenerateTelegramReportCommand(
                chat_id=settings.telegram_allowed_chat_id,
                period_label=label,
                start=start,
                end=end,
            )
        )
        logger.info("Monthly report sent: %s to %s", start, end)
    except Exception:
        logger.exception("Error sending automatic monthly report")


def start_scheduler(use_cases=None) -> None:
    global _use_cases
    _use_cases = use_cases
    scheduler.add_job(
        send_monthly_report,
        CronTrigger(day=1, hour=8, minute=0, timezone="America/Sao_Paulo"),
        id="monthly_report",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Scheduler started (monthly report: 1st at 08:00 BRT)")


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
    logger.info("Scheduler stopped")
