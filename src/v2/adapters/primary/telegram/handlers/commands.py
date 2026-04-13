import calendar
import logging
from datetime import date, timedelta

from src.v2.domain.use_cases.telegram.generate_telegram_report import (
    GenerateTelegramReport,
    GenerateTelegramReportCommand,
)

logger = logging.getLogger(__name__)


async def handle_command(update: dict, use_cases) -> None:
    message = update.get("message") or {}
    chat_id: int = message.get("chat", {}).get("id")
    text: str = message.get("text", "").strip()

    if not chat_id or not text.startswith("/"):
        return

    parts = text.split(maxsplit=1)
    command = parts[0].lstrip("/").split("@")[0].lower()
    args = parts[1].strip() if len(parts) > 1 else ""

    if command == "start":
        await use_cases.process_message._notifier.send_message(
            chat_id,
            "Olá! Envie uma foto de comprovante, PDF ou texto para registrar uma despesa.\n"
            "Use /ajuda para ver todos os comandos.",
        )
    elif command == "ajuda":
        await use_cases.process_message._notifier.send_message(
            chat_id,
            "/relatorio [semana|mes|anterior|MM/AAAA] — relatório de despesas\n"
            "/exportar [semana|mes|anterior|MM/AAAA] — exportar CSV\n"
            "/categorias — listar categorias\n"
            "/categorias add <nome> — adicionar categoria",
        )
    elif command == "relatorio":
        await _handle_report(chat_id, args, use_cases)
    elif command == "exportar":
        await _handle_export(chat_id, args, use_cases)
    elif command == "categorias":
        await _handle_categorias(chat_id, args, use_cases)
    else:
        logger.debug("Unknown command: %s", command)


async def _handle_report(chat_id: int, args: str, use_cases) -> None:
    start, end, label = _parse_period(args)
    generate: GenerateTelegramReport = use_cases.generate_telegram_report
    await generate.execute(
        GenerateTelegramReportCommand(
            chat_id=chat_id,
            period_label=label,
            start=start,
            end=end,
        )
    )


async def _handle_export(chat_id: int, args: str, use_cases) -> None:
    from src.v2.domain.use_cases.reports.export_csv import ExportCsv, ExportCsvQuery
    start, end, label = _parse_period(args)
    export_csv: ExportCsv = use_cases.export_csv
    content = await export_csv.execute(ExportCsvQuery(start=start, end=end))
    filename = f"expenses_{start}_{end}.csv"
    await use_cases.process_message._notifier.send_file(
        chat_id, content, filename, caption=f"Despesas — {label}"
    )


async def _handle_categorias(chat_id: int, args: str, use_cases) -> None:
    if args.lower().startswith("add "):
        name = args[4:].strip()
        if name:
            from src.v2.domain.use_cases.categories.create_category import CreateCategoryCommand
            cat = await use_cases.create_category.execute(
                CreateCategoryCommand(name=name)
            )
            await use_cases.process_message._notifier.send_message(
                chat_id, f"Categoria '{cat.name}' adicionada!"
            )
        return

    categories = await use_cases.list_categories.execute()
    names = "\n".join(f"• {c.name}" for c in categories if c.is_active)
    await use_cases.process_message._notifier.send_message(
        chat_id, f"Categorias disponíveis:\n{names}"
    )


def _parse_period(args: str) -> tuple[date, date, str]:
    """Parse period argument string into (start, end, label)."""
    today = date.today()
    args = args.strip().lower()

    if args == "semana":
        start = today - timedelta(days=today.weekday())
        return start, today, "Esta semana"

    if args == "anterior":
        first_this_month = today.replace(day=1)
        end = first_this_month - timedelta(days=1)
        start = end.replace(day=1)
        return start, end, f"{end.strftime('%B %Y').capitalize()}"

    if args == "" or args == "mes":
        start = today.replace(day=1)
        return start, today, today.strftime("%B %Y").capitalize()

    # MM/AAAA
    try:
        month, year = args.split("/")
        m, y = int(month), int(year)
        last_day = calendar.monthrange(y, m)[1]
        start = date(y, m, 1)
        end = date(y, m, last_day)
        return start, end, f"{start.strftime('%B %Y').capitalize()}"
    except (ValueError, AttributeError):
        pass

    # Default: current month
    return today.replace(day=1), today, today.strftime("%B %Y").capitalize()
