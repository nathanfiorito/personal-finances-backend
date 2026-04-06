import logging

from src.config.settings import settings
from src.handlers.commands import dispatch_command
from src.services import telegram

logger = logging.getLogger(__name__)


def _get_largest_photo_file_id(photos: list[dict]) -> str:
    return max(photos, key=lambda p: p["file_size"])["file_id"]


async def handle_update(update: dict) -> None:
    message = update.get("message") or update.get("edited_message")
    callback_query = update.get("callback_query")

    if callback_query:
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
            await telegram.send_message(chat_id, "Por favor, envie uma imagem ou PDF.")
    elif message.get("text"):
        text: str = message["text"]
        if text.startswith("/"):
            await dispatch_command(chat_id, text)
        else:
            await handle_text(chat_id, text)
    else:
        await telegram.send_message(
            chat_id, "Formato não suportado. Envie uma foto, PDF ou texto."
        )


async def handle_photo(chat_id: int, message: dict) -> None:
    await telegram.send_message(chat_id, "⏳ Processando comprovante...")

    file_id = _get_largest_photo_file_id(message["photo"])
    image_bytes = await telegram.get_file(file_id)

    # POC: retorna payload bruto para validação
    # MVP-M2 irá substituir por: extracted = await extractor.extract_from_image(image_bytes)
    logger.info("Imagem recebida: %d bytes, chat_id=%d", len(image_bytes), chat_id)
    await telegram.send_message(
        chat_id,
        f"📷 Imagem recebida ({len(image_bytes):,} bytes). Extração em breve!",
    )


async def handle_text(chat_id: int, text: str) -> None:
    await telegram.send_message(chat_id, "⏳ Processando...")

    # POC: eco do texto para validação
    # MVP-M2 irá substituir por: extracted = await extractor.extract_from_text(text)
    logger.info("Texto recebido: %r, chat_id=%d", text, chat_id)
    await telegram.send_message(
        chat_id,
        f"✍️ Texto recebido: <i>{text}</i>. Extração em breve!",
    )


async def handle_pdf(chat_id: int, document: dict) -> None:
    await telegram.send_message(chat_id, "⏳ Processando PDF...")

    file_bytes = await telegram.get_file(document["file_id"])

    # MVP-S3 irá substituir por: extracted = await extractor.extract_from_pdf(file_bytes)
    logger.info("PDF recebido: %d bytes, chat_id=%d", len(file_bytes), chat_id)
    await telegram.send_message(
        chat_id,
        f"📄 PDF recebido ({len(file_bytes):,} bytes). Extração em breve!",
    )


async def handle_callback(callback_query: dict) -> None:
    # MVP-M4 irá implementar o fluxo de confirmação
    callback_query_id = callback_query["id"]
    await telegram.answer_callback(callback_query_id)
