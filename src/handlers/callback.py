import logging

from src.models import pending as pending_store
from src.services import telegram

logger = logging.getLogger(__name__)


async def _try_edit(chat_id: int, message_id: int, text: str, **kwargs) -> None:
    """Edit a message; fall back to a new message if the edit fails."""
    try:
        await telegram.edit_message(chat_id, message_id, text, **kwargs)
    except Exception:
        logger.warning("edit_message falhou para chat_id=%s, enviando nova mensagem", chat_id)
        try:
            await telegram.send_message(chat_id, text)
        except Exception:
            logger.error("send_message também falhou para chat_id=%s", chat_id)


async def handle_callback(callback_query: dict) -> None:
    callback_id = callback_query["id"]
    chat_id: int = callback_query["message"]["chat"]["id"]
    message_id: int = callback_query["message"]["message_id"]
    data: str = callback_query.get("data", "")

    if data == "confirm":
        await _handle_confirm(callback_id, chat_id, message_id)
    elif data == "cancel":
        await _handle_cancel(callback_id, chat_id, message_id)
    elif data == "edit_category":
        await _handle_edit_category(callback_id, chat_id, message_id)
    elif data.startswith("set_category:"):
        categoria = data.removeprefix("set_category:")
        await _handle_set_category(callback_id, chat_id, message_id, categoria)
    else:
        await telegram.answer_callback(callback_id)


async def _handle_confirm(callback_id: str, chat_id: int, message_id: int) -> None:
    pending = pending_store.get(chat_id)

    if pending is None:
        await telegram.answer_callback(callback_id, "⏱️ Operação expirada. Envie novamente.")
        await _try_edit(chat_id, message_id, "⏱️ Operação expirada. Envie a despesa novamente.")
        return

    await telegram.answer_callback(callback_id)
    await _try_edit(chat_id, message_id, "⏳ Gravando no banco de dados...")

    saved = False
    try:
        from src.services import database
        await database.save_expense(pending.extracted, pending.categoria)
        saved = True
    except Exception:
        logger.exception("Erro ao salvar despesa")
    finally:
        pending_store.delete(chat_id)

    if saved:
        valor_fmt = f"R$ {pending.extracted.valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        await telegram.send_message(
            chat_id,
            f"✅ Despesa de <b>{valor_fmt}</b> em <b>{pending.categoria}</b> registrada com sucesso!",
        )
    else:
        await telegram.send_message(chat_id, "❌ Erro ao salvar a despesa. Tente novamente.")


async def _handle_cancel(callback_id: str, chat_id: int, message_id: int) -> None:
    pending_store.delete(chat_id)
    await telegram.answer_callback(callback_id, "Cancelado.")
    await _try_edit(chat_id, message_id, "❌ Despesa cancelada.")


async def _handle_edit_category(callback_id: str, chat_id: int, message_id: int) -> None:
    pending = pending_store.get(chat_id)
    if pending is None:
        await telegram.answer_callback(callback_id, "⏱️ Operação expirada. Envie novamente.")
        return

    await telegram.answer_callback(callback_id)
    await _try_edit(
        chat_id,
        message_id,
        "🏷️ Escolha a categoria:",
        reply_markup=telegram._categories_keyboard(),
    )


async def _handle_set_category(
    callback_id: str, chat_id: int, message_id: int, categoria: str
) -> None:
    updated = pending_store.update_categoria(chat_id, categoria)
    if not updated:
        await telegram.answer_callback(callback_id, "⏱️ Operação expirada. Envie novamente.")
        return

    pending = pending_store.get(chat_id)
    await telegram.answer_callback(callback_id, f"Categoria: {categoria}")

    from src.handlers.message import _format_extracted
    await _try_edit(
        chat_id,
        message_id,
        _format_extracted(pending.extracted, pending.categoria),
        reply_markup=telegram._confirmation_keyboard(),
    )
