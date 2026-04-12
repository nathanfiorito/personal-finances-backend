from unittest.mock import AsyncMock, patch

import pytest

from src.v2.adapters.secondary.telegram_api.notifier_adapter import TelegramNotifierAdapter
from src.v2.domain.ports.notifier_port import NotificationButton


@pytest.fixture
def adapter():
    return TelegramNotifierAdapter(bot_token="test-token")


@pytest.mark.asyncio
async def test_send_message_calls_telegram_api(adapter):
    with patch(
        "src.v2.adapters.secondary.telegram_api.notifier_adapter._post",
        new_callable=AsyncMock,
    ) as mock_post:
        mock_post.return_value = None
        await adapter.send_message(chat_id=123, text="Hello")
        mock_post.assert_called_once()
        url, = mock_post.call_args[0]
        assert "sendMessage" in url
        assert mock_post.call_args[1]["json"]["chat_id"] == 123
        assert mock_post.call_args[1]["json"]["text"] == "Hello"


@pytest.mark.asyncio
async def test_send_message_with_buttons_includes_keyboard(adapter):
    buttons = [[NotificationButton(text="Yes", callback_data="yes")]]
    with patch(
        "src.v2.adapters.secondary.telegram_api.notifier_adapter._post",
        new_callable=AsyncMock,
    ) as mock_post:
        mock_post.return_value = None
        await adapter.send_message(chat_id=456, text="Confirm?", buttons=buttons)
        payload = mock_post.call_args[1]["json"]
        assert "reply_markup" in payload
        keyboard = payload["reply_markup"]["inline_keyboard"]
        assert keyboard[0][0]["text"] == "Yes"
        assert keyboard[0][0]["callback_data"] == "yes"


@pytest.mark.asyncio
async def test_answer_callback_sends_correct_payload(adapter):
    with patch(
        "src.v2.adapters.secondary.telegram_api.notifier_adapter._post",
        new_callable=AsyncMock,
    ) as mock_post:
        mock_post.return_value = None
        await adapter.answer_callback(callback_id="cb-001", text="Done!")
        url, = mock_post.call_args[0]
        assert "answerCallbackQuery" in url
        payload = mock_post.call_args[1]["json"]
        assert payload["callback_query_id"] == "cb-001"
        assert payload["text"] == "Done!"
