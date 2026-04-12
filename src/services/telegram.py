import logging

import httpx

from src.config.settings import settings

logger = logging.getLogger(__name__)

TELEGRAM_API = f"https://api.telegram.org/bot{settings.telegram_bot_token}"


def _confirmation_keyboard() -> dict:
    return {
        "inline_keyboard": [[
            {"text": "✅ Confirm", "callback_data": "confirm"},
            {"text": "✏️ Category", "callback_data": "edit_category"},
            {"text": "❌ Cancel", "callback_data": "cancel"},
        ]]
    }


def _duplicate_warning_keyboard() -> dict:
    return {
        "inline_keyboard": [[
            {"text": "💾 Save anyway", "callback_data": "force_confirm"},
            {"text": "❌ Cancel", "callback_data": "cancel"},
        ]]
    }


async def send_message(chat_id: int, text: str, parse_mode: str = "HTML", **kwargs) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{TELEGRAM_API}/sendMessage",
            json={"chat_id": chat_id, "text": text, "parse_mode": parse_mode, **kwargs},
            timeout=10,
        )
        response.raise_for_status()
        return response.json()


async def edit_message(chat_id: int, message_id: int, text: str, **kwargs) -> dict:
    # Remove inline keyboard by default unless caller explicitly passes reply_markup
    if "reply_markup" not in kwargs:
        kwargs["reply_markup"] = {"inline_keyboard": []}
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{TELEGRAM_API}/editMessageText",
            json={
                "chat_id": chat_id,
                "message_id": message_id,
                "text": text,
                "parse_mode": "HTML",
                **kwargs,
            },
            timeout=10,
        )
        # Telegram returns 400 when text+markup didn't change — not a real error
        if response.status_code == 400 and "message is not modified" in response.text:
            return response.json()
        response.raise_for_status()
        return response.json()


async def answer_callback(callback_query_id: str, text: str = "") -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{TELEGRAM_API}/answerCallbackQuery",
            json={"callback_query_id": callback_query_id, "text": text},
            timeout=10,
        )
        response.raise_for_status()
        return response.json()


async def send_document(
    chat_id: int,
    content: bytes,
    filename: str,
    caption: str = "",
    mime_type: str = "text/csv",
) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{TELEGRAM_API}/sendDocument",
            data={"chat_id": str(chat_id), "caption": caption, "parse_mode": "HTML"},
            files={"document": (filename, content, mime_type)},
            timeout=30,
        )
        response.raise_for_status()
        return response.json()


async def get_file(file_id: str) -> bytes:
    async with httpx.AsyncClient() as client:
        # Get file path
        resp = await client.get(f"{TELEGRAM_API}/getFile", params={"file_id": file_id}, timeout=10)
        resp.raise_for_status()
        file_path = resp.json()["result"]["file_path"]

        # Download file
        download_url = (
            f"https://api.telegram.org/file/bot{settings.telegram_bot_token}/{file_path}"
        )
        file_resp = await client.get(download_url, timeout=30)
        file_resp.raise_for_status()
        return file_resp.content
