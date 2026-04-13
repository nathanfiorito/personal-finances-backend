import base64
import logging

from src.v2.domain.use_cases.telegram.process_message import (
    ProcessMessage,
    ProcessMessageCommand,
)

logger = logging.getLogger(__name__)


async def handle_message(update: dict, use_cases) -> None:
    """Route incoming Telegram messages to the ProcessMessage use case."""
    message = update.get("message") or update.get("edited_message") or {}
    chat_id: int = message.get("chat", {}).get("id")
    message_id: int = message.get("message_id")

    if not chat_id:
        return

    process_message: ProcessMessage = use_cases.process_message

    # Image
    if photos := message.get("photo"):
        largest = max(photos, key=lambda p: p.get("file_size", 0))
        file_id = largest["file_id"]
        image_b64 = await _download_image_b64(file_id)
        if image_b64:
            await process_message.execute(
                ProcessMessageCommand(
                    chat_id=chat_id,
                    entry_type="image",
                    image_b64=image_b64,
                    message_id=message_id,
                )
            )
        return

    # Document (PDF)
    if document := message.get("document"):
        mime = document.get("mime_type", "")
        if "pdf" in mime:
            await _handle_pdf(chat_id, message_id, document, process_message)
        else:
            await use_cases.process_message._notifier.send_message(
                chat_id, "Apenas arquivos PDF são suportados."
            )
        return

    # Text
    if text := message.get("text", "").strip():
        await process_message.execute(
            ProcessMessageCommand(
                chat_id=chat_id,
                entry_type="text",
                text=text,
                message_id=message_id,
            )
        )


async def _download_image_b64(file_id: str) -> str | None:
    """Download a Telegram file and return it as base64."""
    try:
        from src.services.telegram import get_file
        content = await get_file(file_id)
        return base64.b64encode(content).decode()
    except Exception:
        logger.exception("Failed to download image file_id=%s", file_id)
        return None


async def _handle_pdf(
    chat_id: int,
    message_id: int,
    document: dict,
    process_message: ProcessMessage,
) -> None:
    try:
        import io

        import pdfplumber

        from src.services.telegram import get_file

        file_id = document["file_id"]
        file_size = document.get("file_size", 0)
        if file_size > 10 * 1024 * 1024:
            await process_message._notifier.send_message(
                chat_id, "PDF muito grande (máx 10 MB)."
            )
            return

        content = await get_file(file_id)

        # Try text extraction
        extracted_text = ""
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            for page in pdf.pages:
                extracted_text += page.extract_text() or ""

        if len(extracted_text.strip()) >= 50:
            await process_message.execute(
                ProcessMessageCommand(
                    chat_id=chat_id,
                    entry_type="pdf",
                    text=extracted_text,
                    message_id=message_id,
                )
            )
        else:
            # Scanned PDF — convert first page to image
            import fitz
            doc = fitz.open(stream=content, filetype="pdf")
            page = doc[0]
            pix = page.get_pixmap(dpi=150)
            image_bytes = pix.tobytes("jpeg")
            image_b64 = base64.b64encode(image_bytes).decode()
            await process_message.execute(
                ProcessMessageCommand(
                    chat_id=chat_id,
                    entry_type="pdf",
                    image_b64=image_b64,
                    message_id=message_id,
                )
            )
    except Exception:
        logger.exception("Failed to process PDF for chat_id=%s", chat_id)
        await process_message._notifier.send_message(
            chat_id, "Não consegui processar o PDF. Tente enviar como imagem ou texto."
        )
