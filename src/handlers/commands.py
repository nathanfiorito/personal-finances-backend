import calendar
import logging
import re
from datetime import date, timedelta

from src.services import telegram

logger = logging.getLogger(__name__)


def _parse_periodo(args: list[str], today: date) -> tuple[date, date] | None:
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
        # Cap end at today for the current month
        if year == today.year and month == today.month:
            end = today
        return date(year, month, 1), end

    return None


async def handle_start(chat_id: int) -> None:
    text = (
        "👋 Olá! Sou o <b>FinBot</b>, seu assistente de controle de despesas.\n\n"
        "Me envie:\n"
        "• 📷 Foto de um comprovante de pagamento\n"
        "• 📄 PDF de nota fiscal\n"
        "• ✍️ Texto livre (ex: <i>\"gastei 50 no mercado\"</i>)\n\n"
        "Use /ajuda para ver todos os comandos."
    )
    await telegram.send_message(chat_id, text)


async def handle_ajuda(chat_id: int) -> None:
    text = (
        "<b>Comandos disponíveis:</b>\n\n"
        "/relatorio — mês corrente\n"
        "/relatorio semana — últimos 7 dias\n"
        "/relatorio anterior — mês anterior\n"
        "/relatorio MM/AAAA — mês específico (ex: <code>03/2025</code>)\n"
        "/ajuda — esta mensagem"
    )
    await telegram.send_message(chat_id, text)


async def handle_relatorio(chat_id: int, args: list[str]) -> None:
    today = date.today()
    periodo = _parse_periodo(args, today)

    if periodo is None:
        await telegram.send_message(
            chat_id,
            "⚠️ Período inválido. Exemplos válidos:\n"
            "/relatorio semana\n"
            "/relatorio anterior\n"
            "/relatorio 03/2025",
        )
        return

    start, end = periodo
    await telegram.send_message(chat_id, "⏳ Gerando relatório...")

    from src.agents import reporter
    report = await reporter.generate_report(start, end)
    await telegram.send_message(chat_id, report)


async def handle_unknown(chat_id: int, command: str) -> None:
    await telegram.send_message(
        chat_id,
        f"Comando <code>{command}</code> não reconhecido. Use /ajuda para ver os comandos disponíveis.",
    )


async def dispatch_command(chat_id: int, text: str) -> None:
    parts = text.split()
    command = parts[0].lower().split("@")[0]  # /cmd@botname → /cmd
    args = parts[1:]

    if command == "/start":
        await handle_start(chat_id)
    elif command == "/ajuda":
        await handle_ajuda(chat_id)
    elif command == "/relatorio":
        await handle_relatorio(chat_id, args)
    else:
        await handle_unknown(chat_id, command)
