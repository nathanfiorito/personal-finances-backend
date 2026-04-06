import calendar
import csv
import io
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
        if year == today.year and month == today.month:
            end = today
        return date(year, month, 1), end

    return None


def _generate_csv(expenses: list) -> bytes:
    output = io.StringIO()
    fieldnames = ["data", "valor", "estabelecimento", "categoria", "descricao", "cnpj", "tipo_entrada"]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for e in expenses:
        writer.writerow({
            "data": e.data.strftime("%d/%m/%Y"),
            "valor": str(e.valor).replace(".", ","),
            "estabelecimento": e.estabelecimento or "",
            "categoria": e.categoria,
            "descricao": e.descricao or "",
            "cnpj": e.cnpj or "",
            "tipo_entrada": e.tipo_entrada,
        })
    return b"\xef\xbb\xbf" + output.getvalue().encode("utf-8")  # UTF-8 BOM for Excel


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
        "/relatorio MM/AAAA — mês específico (ex: <code>03/2025</code>)\n\n"
        "/exportar — exportar despesas do mês como CSV\n"
        "/exportar anterior — CSV do mês anterior\n"
        "/exportar MM/AAAA — CSV de um mês específico\n\n"
        "/categorias — listar categorias disponíveis\n"
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


async def handle_exportar(chat_id: int, args: list[str]) -> None:
    today = date.today()
    periodo = _parse_periodo(args, today)

    if periodo is None:
        await telegram.send_message(
            chat_id,
            "⚠️ Período inválido. Exemplos válidos:\n"
            "/exportar mes\n"
            "/exportar anterior\n"
            "/exportar 03/2025",
        )
        return

    start, end = periodo
    await telegram.send_message(chat_id, "⏳ Gerando exportação...")

    from src.services import database
    expenses = await database.get_expenses_by_period(start, end)

    if not expenses:
        await telegram.send_message(chat_id, "📊 Nenhuma despesa registrada no período selecionado.")
        return

    csv_bytes = _generate_csv(expenses)
    filename = f"despesas_{start.strftime('%m-%Y')}.csv"
    caption = f"📎 <b>{len(expenses)} despesas</b> — {start.strftime('%d/%m/%Y')} a {end.strftime('%d/%m/%Y')}"
    await telegram.send_document(chat_id, csv_bytes, filename, caption)


async def handle_categorias(chat_id: int) -> None:
    from src.services import database
    try:
        categories = await database.get_active_categories()
    except Exception:
        logger.warning("Falha ao buscar categorias do banco, usando padrão")
        from src.agents.categorizer import CATEGORIES
        categories = CATEGORIES

    lines = [f"  • {cat}" for cat in categories]
    text = "<b>Categorias disponíveis:</b>\n\n" + "\n".join(lines)
    await telegram.send_message(chat_id, text)


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
    elif command == "/exportar":
        await handle_exportar(chat_id, args)
    elif command == "/categorias":
        await handle_categorias(chat_id)
    else:
        await handle_unknown(chat_id, command)
