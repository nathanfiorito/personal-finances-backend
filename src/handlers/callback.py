import logging

from src.models import pending as pending_store
from src.services import telegram

logger = logging.getLogger(__name__)


async def _try_edit(chat_id: int, message_id: int, text: str, **kwargs) -> None:
    """Edit a message; fall back to a new message if the edit fails."""
    try:
        await telegram.edit_message(chat_id, message_id, text, **kwargs)
    except Exception:
        logger.warning("edit_message failed for chat_id=%s, sending new message", chat_id)
        try:
            await telegram.send_message(chat_id, text)
        except Exception:
            logger.error("send_message also failed for chat_id=%s", chat_id)


async def _do_save(chat_id: int, message_id: int, pending) -> None:
    """Persists the pending expense and sends the result to the user."""
    await _try_edit(chat_id, message_id, "⏳ Saving to database...")

    saved = False
    try:
        from src.services import database
        await database.save_expense(pending.extracted, pending.category)
        saved = True
    except Exception:
        logger.exception("Error saving expense")
    finally:
        pending_store.delete(chat_id)

    if saved:
        amount_fmt = f"R$ {pending.extracted.amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")  # noqa: E501
        await telegram.send_message(
            chat_id,
            f"✅ Expense of <b>{amount_fmt}</b> in <b>{pending.category}</b> registered successfully!",  # noqa: E501
        )
    else:
        await telegram.send_message(chat_id, "❌ Error saving expense. Try again.")


async def handle_callback(callback_query: dict) -> None:
    callback_id = callback_query["id"]
    chat_id: int = callback_query["message"]["chat"]["id"]
    message_id: int = callback_query["message"]["message_id"]
    data: str = callback_query.get("data", "")

    if data == "confirm":
        await _handle_confirm(callback_id, chat_id, message_id)
    elif data == "force_confirm":
        await _handle_force_confirm(callback_id, chat_id, message_id)
    elif data == "cancel":
        await _handle_cancel(callback_id, chat_id, message_id)
    elif data == "edit_category":
        await _handle_edit_category(callback_id, chat_id, message_id)
    elif data.startswith("set_category:"):
        category = data.removeprefix("set_category:")
        await _handle_set_category(callback_id, chat_id, message_id, category)
    else:
        await telegram.answer_callback(callback_id)


async def _handle_confirm(callback_id: str, chat_id: int, message_id: int) -> None:
    pending = pending_store.get(chat_id)
    if pending is None:
        await telegram.answer_callback(callback_id, "⏱️ Operation expired. Send again.")
        await _try_edit(chat_id, message_id, "⏱️ Operation expired. Send the expense again.")
        return

    await telegram.answer_callback(callback_id)
    await _try_edit(chat_id, message_id, "⏳ Checking for duplicates...")

    duplicate_reason: str | None = None
    try:
        from src.agents.duplicate_checker import check_duplicate
        from src.services import database
        recent = await database.get_recent_expenses(3)
        duplicate_reason = await check_duplicate(pending.extracted, recent)
    except Exception:
        logger.warning("Duplicate check failed, proceeding with save")

    if duplicate_reason:
        await _try_edit(
            chat_id,
            message_id,
            f"⚠️ <b>Possible duplicate detected</b>\n\n{duplicate_reason}\n\nSave anyway?",
            reply_markup=telegram._duplicate_warning_keyboard(),
        )
        return

    await _do_save(chat_id, message_id, pending)


async def _handle_force_confirm(callback_id: str, chat_id: int, message_id: int) -> None:
    pending = pending_store.get(chat_id)
    if pending is None:
        await telegram.answer_callback(callback_id, "⏱️ Operation expired. Send again.")
        await _try_edit(chat_id, message_id, "⏱️ Operation expired. Send the expense again.")
        return

    await telegram.answer_callback(callback_id)
    await _do_save(chat_id, message_id, pending)


async def _handle_cancel(callback_id: str, chat_id: int, message_id: int) -> None:
    pending_store.delete(chat_id)
    await telegram.answer_callback(callback_id, "Canceled.")
    await _try_edit(chat_id, message_id, "❌ Expense canceled.")


async def _handle_edit_category(callback_id: str, chat_id: int, message_id: int) -> None:
    pending = pending_store.get(chat_id)
    if pending is None:
        await telegram.answer_callback(callback_id, "⏱️ Operation expired. Send again.")
        return

    await telegram.answer_callback(callback_id)
    await _try_edit(
        chat_id,
        message_id,
        "🏷️ Choose a category:",
        reply_markup=telegram._categories_keyboard(),
    )


async def _handle_set_category(
    callback_id: str, chat_id: int, message_id: int, category: str
) -> None:
    updated = pending_store.update_category(chat_id, category)
    if not updated:
        await telegram.answer_callback(callback_id, "⏱️ Operation expired. Send again.")
        return

    pending = pending_store.get(chat_id)
    await telegram.answer_callback(callback_id, f"Category: {category}")

    from src.handlers.message import _format_extracted
    await _try_edit(
        chat_id,
        message_id,
        _format_extracted(pending.extracted, pending.category),
        reply_markup=telegram._confirmation_keyboard(),
    )
