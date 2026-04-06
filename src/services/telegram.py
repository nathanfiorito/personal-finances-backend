import logging

import httpx

from src.config.settings import settings

logger = logging.getLogger(__name__)

TELEGRAM_API = f"https://api.telegram.org/bot{settings.telegram_bot_token}"


def _confirmation_keyboard() -> dict:
    return {
        "inline_keyboard": [[
            {"text": "✅ Confirmar", "callback_data": "confirm"},
            {"text": "✏️ Categoria", "callback_data": "edit_category"},
            {"text": "❌ Cancelar", "callback_data": "cancel"},
        ]]
    }


def _categories_keyboard() -> dict:
    from src.agents.categorizer import CATEGORIES
    rows = []
    for i in range(0, len(CATEGORIES), 2):
        row = [{"text": cat, "callback_data": f"set_category:{cat}"} for cat in CATEGORIES[i:i+2]]
        rows.append(row)
    return {"inline_keyboard": rows}


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
