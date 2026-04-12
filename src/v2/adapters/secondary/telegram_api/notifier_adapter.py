import logging
from typing import Any

import httpx

from src.v2.domain.ports.notifier_port import NotificationButton, NotifierPort

logger = logging.getLogger(__name__)


async def _post(url: str, **kwargs: Any) -> None:
    """Fire-and-forget POST to the Telegram Bot API."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(url, **kwargs)
        if not response.is_success:
            logger.warning(
                "Telegram API error %d: %s", response.status_code, response.text[:200]
            )


def _build_keyboard(
    buttons: list[list[NotificationButton]],
) -> dict:
    return {
        "inline_keyboard": [
            [{"text": btn.text, "callback_data": btn.callback_data} for btn in row]
            for row in buttons
        ]
    }


class TelegramNotifierAdapter(NotifierPort):
    def __init__(self, bot_token: str, base_url: str = "https://api.telegram.org") -> None:
        self._base = f"{base_url}/bot{bot_token}"

    async def send_message(
        self,
        chat_id: int,
        text: str,
        parse_mode: str | None = None,
        buttons: list[list[NotificationButton]] | None = None,
    ) -> None:
        payload: dict = {"chat_id": chat_id, "text": text}
        if parse_mode:
            payload["parse_mode"] = parse_mode
        if buttons:
            payload["reply_markup"] = _build_keyboard(buttons)
        await _post(f"{self._base}/sendMessage", json=payload)

    async def send_file(
        self,
        chat_id: int,
        content: bytes,
        filename: str,
        caption: str,
    ) -> None:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self._base}/sendDocument",
                data={"chat_id": chat_id, "caption": caption},
                files={"document": (filename, content, "text/csv")},
            )
            if not response.is_success:
                logger.warning(
                    "Telegram sendDocument error %d: %s",
                    response.status_code,
                    response.text[:200],
                )

    async def answer_callback(
        self,
        callback_id: str,
        text: str | None = None,
    ) -> None:
        payload: dict = {"callback_query_id": callback_id}
        if text:
            payload["text"] = text
        await _post(f"{self._base}/answerCallbackQuery", json=payload)

    async def edit_message(
        self,
        chat_id: int,
        message_id: int,
        text: str,
        parse_mode: str | None = None,
        buttons: list[list[NotificationButton]] | None = None,
    ) -> None:
        payload: dict = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
        }
        if parse_mode:
            payload["parse_mode"] = parse_mode
        if buttons:
            payload["reply_markup"] = _build_keyboard(buttons)
        else:
            payload["reply_markup"] = {"inline_keyboard": []}
        try:
            await _post(f"{self._base}/editMessageText", json=payload)
        except Exception:
            logger.warning(
                "editMessageText failed for chat_id=%s — sending new message", chat_id
            )
            await self.send_message(chat_id, text, parse_mode=parse_mode)
