import calendar
import logging
from datetime import date

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from src.config.settings import settings
from src.services import telegram

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler(timezone="America/Sao_Paulo")


async def send_monthly_report() -> None:
    """Sends the previous month's report. Called automatically on the 1st of each month."""
    try:
        today = date.today()
        # Previous month
        if today.month == 1:
            year, month = today.year - 1, 12
        else:
            year, month = today.year, today.month - 1

        start = date(year, month, 1)
        end = date(year, month, calendar.monthrange(year, month)[1])

        from src.agents import reporter
        report = await reporter.generate_report(start, end)
        await telegram.send_message(settings.telegram_allowed_chat_id, report)
        logger.info("Monthly report sent: %s to %s", start, end)
    except Exception:
        logger.exception("Error sending automatic monthly report")


def start_scheduler() -> None:
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
