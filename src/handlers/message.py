import logging

from src.agents import categorizer, extractor
from src.agents.extractor import ExtractionError
from src.handlers.commands import dispatch_command
from src.models import pending as pending_store
from src.models.expense import ExtractedExpense
from src.services import telegram
from src.services.llm import LLMRateLimitError, LLMTimeoutError

logger = logging.getLogger(__name__)


def _get_largest_photo_file_id(photos: list[dict]) -> str:
    return max(photos, key=lambda p: p["file_size"])["file_id"]


def _format_extracted(expense: ExtractedExpense, category: str) -> str:
    date_fmt = expense.date.strftime("%d/%m/%Y")
    amount_fmt = f"R$ {expense.amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    confidence_pct = int(expense.confidence * 100)
    type_label = "Income" if expense.transaction_type == "income" else "Expense"
    type_emoji = "📈" if expense.transaction_type == "income" else "📉"

    lines = [
        f"{type_emoji} <b>{type_label} detected:</b>",
        f"💰 Amount: <b>{amount_fmt}</b>",
        f"📅 Date: {date_fmt}",
    ]
    if expense.establishment:
        lines.append(f"🏪 Establishment: {expense.establishment}")
    if expense.description:
        lines.append(f"📝 Description: {expense.description}")
    if expense.tax_id:
        lines.append(f"🔢 Tax ID: {expense.tax_id}")
    lines.append(f"🏷️ Category: <b>{category}</b>")
    lines.append(f"\n🎯 Confidence: {confidence_pct}%")
    return "\n".join(lines)


async def _send_confirmation(chat_id: int, expense: ExtractedExpense, category: str) -> None:
    msg = await telegram.send_message(
        chat_id,
        _format_extracted(expense, category),
        reply_markup=telegram._confirmation_keyboard(),
    )
    message_id = msg["result"]["message_id"]
    pending_store.save(chat_id, expense, category, message_id)


async def handle_update(update: dict) -> None:
    message = update.get("message") or update.get("edited_message")
    callback_query = update.get("callback_query")

    if callback_query:
        from src.handlers.callback import handle_callback
        await handle_callback(callback_query)
        return

    if not message:
        return

    chat_id: int = message["chat"]["id"]

    if message.get("photo"):
        await handle_photo(chat_id, message)
    elif message.get("document"):
        doc = message["document"]
        if doc.get("mime_type") == "application/pdf":
            await handle_pdf(chat_id, doc)
        else:
            await telegram.send_message(chat_id, "Please send an image or PDF.")
    elif message.get("text"):
        text: str = message["text"]
        if text.startswith("/"):
            await dispatch_command(chat_id, text)
        else:
            await handle_text(chat_id, text)
    else:
        await telegram.send_message(
            chat_id, "Unsupported format. Send a photo, PDF, or text."
        )


async def handle_photo(chat_id: int, message: dict) -> None:
    await telegram.send_message(chat_id, "⏳ Analyzing receipt...")
    file_id = _get_largest_photo_file_id(message["photo"])

    try:
        image_bytes = await telegram.get_file(file_id)
        expense = await extractor.extract_from_image(image_bytes)
        category = await categorizer.categorize(expense)
        await _send_confirmation(chat_id, expense, category)
    except LLMTimeoutError:
        await telegram.send_message(chat_id, "⏱️ The AI service took too long. Try again.")
    except LLMRateLimitError:
        await telegram.send_message(chat_id, "⚠️ Too many requests. Wait a few seconds and try again.")
    except ExtractionError as e:
        logger.warning("Image extraction failed: %s", e)
        await telegram.send_message(
            chat_id,
            "⚠️ Could not extract data from this receipt. "
            "Try sending a clearer photo or describe the expense in text.",
        )
    except Exception:
        logger.exception("Unexpected error processing image")
        await telegram.send_message(chat_id, "❌ An unexpected error occurred. Try again.")


async def handle_text(chat_id: int, text: str) -> None:
    await telegram.send_message(chat_id, "⏳ Processing...")

    try:
        expense = await extractor.extract_from_text(text)
        category = await categorizer.categorize(expense)
        await _send_confirmation(chat_id, expense, category)
    except LLMTimeoutError:
        await telegram.send_message(chat_id, "⏱️ The AI service took too long. Try again.")
    except LLMRateLimitError:
        await telegram.send_message(chat_id, "⚠️ Too many requests. Wait a few seconds and try again.")
    except ExtractionError as e:
        logger.warning("Text extraction failed: %s", e)
        await telegram.send_message(
            chat_id,
            "⚠️ I didn't understand the expense. Try something like: <i>\"spent 50 at the grocery store\"</i>",
        )
    except Exception:
        logger.exception("Unexpected error processing text")
        await telegram.send_message(chat_id, "❌ An unexpected error occurred. Try again.")


async def handle_pdf(chat_id: int, document: dict) -> None:
    if document.get("file_size", 0) > 10 * 1024 * 1024:
        await telegram.send_message(
            chat_id, "⚠️ PDF too large (max 10MB). Try taking a photo of the document."
        )
        return

    await telegram.send_message(chat_id, "⏳ Processing PDF...")

    try:
        pdf_bytes = await telegram.get_file(document["file_id"])
        expense = await extractor.extract_from_pdf(pdf_bytes)
        category = await categorizer.categorize(expense)
        await _send_confirmation(chat_id, expense, category)
    except LLMTimeoutError:
        await telegram.send_message(chat_id, "⏱️ The AI service took too long. Try again.")
    except LLMRateLimitError:
        await telegram.send_message(chat_id, "⚠️ Too many requests. Wait a few seconds and try again.")
    except ExtractionError as e:
        logger.warning("PDF extraction failed: %s", e)
        await telegram.send_message(
            chat_id,
            "⚠️ Could not extract data from this PDF. Try taking a photo of the document.",
        )
    except Exception:
        logger.exception("Unexpected error processing PDF")
        await telegram.send_message(chat_id, "❌ An unexpected error occurred. Try again.")
