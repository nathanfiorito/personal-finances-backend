import logging

from src.v2.domain.use_cases.telegram.cancel_expense import CancelExpenseCommand
from src.v2.domain.use_cases.telegram.change_category import ChangeCategoryCommand
from src.v2.domain.use_cases.telegram.confirm_expense import ConfirmExpenseCommand

logger = logging.getLogger(__name__)


async def handle_callback(update: dict, use_cases) -> None:
    callback_query = update.get("callback_query", {})
    callback_id: str = callback_query.get("id", "")
    message = callback_query.get("message", {})
    chat_id: int = message.get("chat", {}).get("id")
    message_id: int = message.get("message_id")
    data: str = callback_query.get("data", "")

    notifier = use_cases.process_message._notifier
    await notifier.answer_callback(callback_id)

    if data == "confirm":
        await use_cases.confirm_expense.execute(
            ConfirmExpenseCommand(
                chat_id=chat_id,
                message_id=message_id,
                skip_duplicate_check=False,
            )
        )

    elif data == "force_confirm":
        await use_cases.confirm_expense.execute(
            ConfirmExpenseCommand(
                chat_id=chat_id,
                message_id=message_id,
                skip_duplicate_check=True,
            )
        )

    elif data == "cancel":
        await use_cases.cancel_expense.execute(
            CancelExpenseCommand(chat_id=chat_id, message_id=message_id)
        )

    elif data == "edit_category":
        categories = await use_cases.list_categories.execute()
        from src.v2.domain.ports.notifier_port import NotificationButton
        rows = []
        row = []
        for cat in categories:
            if cat.is_active:
                row.append(
                    NotificationButton(
                        text=cat.name,
                        callback_data=f"set_category:{cat.id}:{cat.name}",
                    )
                )
                if len(row) == 2:
                    rows.append(row)
                    row = []
        if row:
            rows.append(row)
        await notifier.edit_message(
            chat_id, message_id, "Escolha a categoria:", buttons=rows
        )

    elif data.startswith("set_category:"):
        # format: set_category:{id}:{name}
        parts = data.split(":", 2)
        if len(parts) == 3:
            try:
                category_id = int(parts[1])
                category_name = parts[2]
                await use_cases.change_category.execute(
                    ChangeCategoryCommand(
                        chat_id=chat_id,
                        message_id=message_id,
                        new_category=category_name,
                        new_category_id=category_id,
                    )
                )
            except (ValueError, IndexError):
                logger.warning("Malformed set_category callback: %r", data)
    else:
        logger.debug("Unhandled callback data: %r", data)
