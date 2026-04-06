import pytest
from fastapi.testclient import TestClient

from src.main import app, _extract_chat_id

client = TestClient(app)

VALID_SECRET = "test-secret"
ALLOWED_CHAT_ID = 12345

# Patch settings for tests
@pytest.fixture(autouse=True)
def patch_settings(monkeypatch):
    import src.main as main_module
    import src.config.settings as settings_module

    monkeypatch.setattr(settings_module.settings, "telegram_webhook_secret", VALID_SECRET)
    monkeypatch.setattr(settings_module.settings, "telegram_allowed_chat_id", ALLOWED_CHAT_ID)
    monkeypatch.setattr(main_module.settings, "telegram_webhook_secret", VALID_SECRET)
    monkeypatch.setattr(main_module.settings, "telegram_allowed_chat_id", ALLOWED_CHAT_ID)


def _make_text_update(chat_id: int, text: str) -> dict:
    return {
        "update_id": 1,
        "message": {
            "message_id": 1,
            "chat": {"id": chat_id, "type": "private"},
            "from": {"id": chat_id, "is_bot": False, "first_name": "Test"},
            "text": text,
            "date": 1700000000,
        },
    }


class TestWebhookSecurity:
    def test_missing_secret_returns_403(self):
        response = client.post("/webhook", json=_make_text_update(ALLOWED_CHAT_ID, "oi"))
        assert response.status_code == 403

    def test_wrong_secret_returns_403(self):
        response = client.post(
            "/webhook",
            json=_make_text_update(ALLOWED_CHAT_ID, "oi"),
            headers={"X-Telegram-Bot-Api-Secret-Token": "wrong-secret"},
        )
        assert response.status_code == 403

    def test_valid_secret_accepted(self, mocker):
        mocker.patch("src.handlers.message.handle_update")
        response = client.post(
            "/webhook",
            json=_make_text_update(ALLOWED_CHAT_ID, "oi"),
            headers={"X-Telegram-Bot-Api-Secret-Token": VALID_SECRET},
        )
        assert response.status_code == 200

    def test_unauthorized_chat_id_ignored(self, mocker):
        mock_handle = mocker.patch("src.handlers.message.handle_update")
        response = client.post(
            "/webhook",
            json=_make_text_update(99999, "oi"),  # chat_id não autorizado
            headers={"X-Telegram-Bot-Api-Secret-Token": VALID_SECRET},
        )
        assert response.status_code == 200
        mock_handle.assert_not_called()


class TestExtractChatId:
    def test_from_message(self):
        update = {"message": {"chat": {"id": 123}}}
        assert _extract_chat_id(update) == 123

    def test_from_callback_query(self):
        update = {"callback_query": {"message": {"chat": {"id": 456}}}}
        assert _extract_chat_id(update) == 456

    def test_unknown_update_returns_none(self):
        assert _extract_chat_id({"unknown": {}}) is None


class TestHealthEndpoint:
    def test_health_ok(self):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
