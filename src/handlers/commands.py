import calendar
import csv
import io
import logging
import re
from datetime import date, timedelta

from src.services import telegram

logger = logging.getLogger(__name__)


def _parse_period(args: list[str], today: date) -> tuple[date, date] | None:
    """
    Parses the period argument(s) and returns (start, end).
    Returns None if the input is invalid.

    Supported formats:
      (empty)          → current month
      mes              → current month
      semana           → last 7 days
      anterior         → previous month
      MM/AAAA          → specific month (e.g. 03/2025)
    """
    arg = args[0].lower() if args else "mes"

    if arg == "semana":
        return today - timedelta(days=7), today

    if arg in ("mes", "mês"):
        return today.replace(day=1), today

    if arg == "anterior":
        year, month = (today.year - 1, 12) if today.month == 1 else (today.year, today.month - 1)
        return date(year, month, 1), date(year, month, calendar.monthrange(year, month)[1])

    if re.fullmatch(r"\d{2}/\d{4}", arg):
        month, year = int(arg[:2]), int(arg[3:])
        if not (1 <= month <= 12 and year >= 2000):
            return None
        last_day = calendar.monthrange(year, month)[1]
        end = date(year, month, last_day)
        if year == today.year and month == today.month:
            end = today
        return date(year, month, 1), end

    return None


def _generate_csv(expenses: list) -> bytes:
    output = io.StringIO()
    fieldnames = ["date", "amount", "establishment", "category", "description", "tax_id", "entry_type"]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for e in expenses:
        writer.writerow({
            "date": e.date.strftime("%d/%m/%Y"),
            "amount": str(e.amount).replace(".", ","),
            "establishment": e.establishment or "",
            "category": e.category,
            "description": e.description or "",
            "tax_id": e.tax_id or "",
            "entry_type": e.entry_type,
        })
    return b"\xef\xbb\xbf" + output.getvalue().encode("utf-8")  # UTF-8 BOM for Excel


async def handle_start(chat_id: int) -> None:
    text = (
        "👋 Hello! I'm <b>FinBot</b>, your expense tracking assistant.\n\n"
        "Send me:\n"
        "• 📷 A photo of a payment receipt\n"
        "• 📄 A PDF invoice\n"
        "• ✍️ Free text (e.g.: <i>\"spent 50 at the grocery store\"</i>)\n\n"
        "Use /help to see all commands."
    )
    await telegram.send_message(chat_id, text)


async def handle_help(chat_id: int) -> None:
    text = (
        "<b>Available commands:</b>\n\n"
        "/report — current month\n"
        "/report week — last 7 days\n"
        "/report previous — previous month\n"
        "/report MM/YYYY — specific month (e.g. <code>03/2025</code>)\n\n"
        "/export — export expenses for the month as CSV\n"
        "/export previous — previous month CSV\n"
        "/export MM/YYYY — specific month CSV\n\n"
        "/categories — list available categories\n"
        "/help — this message"
    )
    await telegram.send_message(chat_id, text)


async def handle_report(chat_id: int, args: list[str]) -> None:
    today = date.today()
    period = _parse_period(args, today)

    if period is None:
        await telegram.send_message(
            chat_id,
            "⚠️ Invalid period. Valid examples:\n"
            "/report week\n"
            "/report previous\n"
            "/report 03/2025",
        )
        return

    start, end = period
    await telegram.send_message(chat_id, "⏳ Generating report...")

    from src.agents import reporter
    report = await reporter.generate_report(start, end)
    await telegram.send_message(chat_id, report)


async def handle_export(chat_id: int, args: list[str]) -> None:
    today = date.today()
    period = _parse_period(args, today)

    if period is None:
        await telegram.send_message(
            chat_id,
            "⚠️ Invalid period. Valid examples:\n"
            "/export month\n"
            "/export previous\n"
            "/export 03/2025",
        )
        return

    start, end = period
    await telegram.send_message(chat_id, "⏳ Generating export...")

    from src.services import database
    expenses = await database.get_expenses_by_period(start, end)

    if not expenses:
        await telegram.send_message(chat_id, "📊 No expenses registered for the selected period.")
        return

    csv_bytes = _generate_csv(expenses)
    filename = f"expenses_{start.strftime('%m-%Y')}.csv"
    caption = f"📎 <b>{len(expenses)} expenses</b> — {start.strftime('%d/%m/%Y')} to {end.strftime('%d/%m/%Y')}"
    await telegram.send_document(chat_id, csv_bytes, filename, caption)


async def handle_categories(chat_id: int, args: list[str]) -> None:
    if args and args[0].lower() == "add":
        await _handle_category_add(chat_id, args[1:])
        return

    from src.services import database
    try:
        categories = await database.get_active_categories()
    except Exception:
        logger.warning("Failed to fetch categories from DB, using defaults")
        from src.agents.categorizer import CATEGORIES
        categories = CATEGORIES

    lines = [f"  • {cat}" for cat in categories]
    text = (
        "<b>Available categories:</b>\n\n"
        + "\n".join(lines)
        + "\n\nTo add: /categories add <i>Name</i>"
    )
    await telegram.send_message(chat_id, text)


async def _handle_category_add(chat_id: int, args: list[str]) -> None:
    name = " ".join(args).strip()
    if not name:
        await telegram.send_message(
            chat_id, "⚠️ Provide the category name. E.g.: /categories add Investments"
        )
        return

    from src.agents.categorizer import invalidate_cache
    from src.services import database
    try:
        await database.add_category(name)
        invalidate_cache()
        await telegram.send_message(chat_id, f"✅ Category <b>{name}</b> added successfully!")
    except Exception as e:
        if "duplicate" in str(e).lower() or "unique" in str(e).lower():
            await telegram.send_message(chat_id, f"⚠️ Category <b>{name}</b> already exists.")
        else:
            logger.exception("Error adding category")
            await telegram.send_message(chat_id, "❌ Error adding category. Try again.")


async def handle_unknown(chat_id: int, command: str) -> None:
    await telegram.send_message(
        chat_id,
        f"Command <code>{command}</code> not recognized. Use /help to see available commands.",
    )


async def dispatch_command(chat_id: int, text: str) -> None:
    parts = text.split()
    command = parts[0].lower().split("@")[0]  # /cmd@botname → /cmd
    args = parts[1:]

    if command == "/start":
        await handle_start(chat_id)
    elif command in ("/ajuda", "/help"):
        await handle_help(chat_id)
    elif command in ("/relatorio", "/report"):
        await handle_report(chat_id, args)
    elif command in ("/exportar", "/export"):
        await handle_export(chat_id, args)
    elif command in ("/categorias", "/categories"):
        await handle_categories(chat_id, args)
    else:
        await handle_unknown(chat_id, command)
