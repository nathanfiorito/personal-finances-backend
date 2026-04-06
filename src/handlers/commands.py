import logging
from datetime import date, timedelta

from src.services import telegram

logger = logging.getLogger(__name__)


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
        "/start — mensagem de boas-vindas\n"
        "/relatorio semana — relatório dos últimos 7 dias\n"
        "/relatorio mes — relatório do mês corrente\n"
        "/ajuda — esta mensagem"
    )
    await telegram.send_message(chat_id, text)


async def handle_relatorio(chat_id: int, args: list[str]) -> None:
    periodo_arg = args[0].lower() if args else "mes"
    today = date.today()

    if periodo_arg == "semana":
        start = today - timedelta(days=7)
        end = today
    else:
        start = today.replace(day=1)
        end = today

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
