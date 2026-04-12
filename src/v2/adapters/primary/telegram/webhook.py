import logging

from src.v2.adapters.primary.telegram.handlers.callback import handle_callback
from src.v2.adapters.primary.telegram.handlers.commands import handle_command
from src.v2.adapters.primary.telegram.handlers.message import handle_message

logger = logging.getLogger(__name__)


async def handle_update(update: dict, use_cases) -> None:
    """Route a Telegram update to the correct handler."""
    if "callback_query" in update:
        await handle_callback(update, use_cases)
        return

    message = update.get("message") or update.get("edited_message") or {}
    text: str = message.get("text", "")

    if text.startswith("/"):
        await handle_command(update, use_cases)
    else:
        await handle_message(update, use_cases)
