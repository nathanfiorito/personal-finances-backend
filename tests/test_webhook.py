import pytest
from fastapi.testclient import TestClient

from src.main import app, _extract_chat_id

client = TestClient(app)

VALID_SECRET = "test-secret"
ALLOWED_CHAT_ID = 12345
HEADERS = {"X-Telegram-Bot-Api-Secret-Token": VALID_SECRET}


@pytest.fixture(autouse=True)
def patch_settings(monkeypatch):
    import src.main as main_module
    import src.config.settings as settings_module

    monkeypatch.setattr(settings_module.settings, "telegram_webhook_secret", VALID_SECRET)
    monkeypatch.setattr(settings_module.settings, "telegram_allowed_chat_id", ALLOWED_CHAT_ID)
    monkeypatch.setattr(main_module.settings, "telegram_webhook_secret", VALID_SECRET)
    monkeypatch.setattr(main_module.settings, "telegram_allowed_chat_id", ALLOWED_CHAT_ID)


# --- Helpers ---

def _message_update(chat_id: int, **message_fields) -> dict:
    return {
        "update_id": 1,
        "message": {
            "message_id": 1,
            "chat": {"id": chat_id, "type": "private"},
            "from": {"id": chat_id, "is_bot": False, "first_name": "Test"},
            "date": 1700000000,
            **message_fields,
        },
    }

def _text_update(chat_id: int, text: str) -> dict:
    return _message_update(chat_id, text=text)

def _photo_update(chat_id: int) -> dict:
    return _message_update(chat_id, photo=[
        {"file_id": "small", "file_unique_id": "s1", "width": 100, "height": 100, "file_size": 1000},
        {"file_id": "large", "file_unique_id": "l1", "width": 800, "height": 600, "file_size": 80000},
    ])

def _pdf_update(chat_id: int) -> dict:
    return _message_update(chat_id, document={
        "file_id": "doc123",
        "file_unique_id": "d1",
        "file_name": "nota.pdf",
        "mime_type": "application/pdf",
        "file_size": 50000,
    })

def _callback_update(chat_id: int, data: str) -> dict:
    return {
        "update_id": 1,
        "callback_query": {
            "id": "cq1",
            "from": {"id": chat_id, "is_bot": False, "first_name": "Test"},
            "message": {"message_id": 1, "chat": {"id": chat_id, "type": "private"}},
            "data": data,
        },
    }


# --- Segurança ---

class TestSecurity:
    def test_missing_secret_returns_403(self):
        response = client.post("/webhook", json=_text_update(ALLOWED_CHAT_ID, "oi"))
        assert response.status_code == 403

    def test_wrong_secret_returns_403(self):
        response = client.post(
            "/webhook",
            json=_text_update(ALLOWED_CHAT_ID, "oi"),
            headers={"X-Telegram-Bot-Api-Secret-Token": "wrong"},
        )
        assert response.status_code == 403

    def test_valid_secret_returns_200(self, mocker):
        # Patch where main.py bound the reference
        mocker.patch("src.main.handle_update")
        response = client.post("/webhook", json=_text_update(ALLOWED_CHAT_ID, "oi"), headers=HEADERS)
        assert response.status_code == 200

    def test_unauthorized_chat_id_ignored(self, mocker):
        mock_handle = mocker.patch("src.main.handle_update")
        response = client.post("/webhook", json=_text_update(99999, "oi"), headers=HEADERS)
        assert response.status_code == 200
        mock_handle.assert_not_called()

    def test_authorized_chat_id_processed(self, mocker):
        mock_handle = mocker.patch("src.main.handle_update")
        client.post("/webhook", json=_text_update(ALLOWED_CHAT_ID, "oi"), headers=HEADERS)
        mock_handle.assert_called_once()


# --- Roteamento ---

class TestRouting:
    @pytest.fixture(autouse=True)
    def mock_telegram(self, mocker):
        # Evita chamadas reais à API do Telegram em todos os testes de roteamento
        mocker.patch("src.handlers.message.telegram.send_message")
        mocker.patch("src.handlers.message.telegram.answer_callback")

    def test_text_message_calls_handle_text(self, mocker):
        mock_text = mocker.patch("src.handlers.message.handle_text")
        client.post("/webhook", json=_text_update(ALLOWED_CHAT_ID, "gastei 50 no mercado"), headers=HEADERS)
        mock_text.assert_called_once_with(ALLOWED_CHAT_ID, "gastei 50 no mercado")

    def test_command_calls_dispatch(self, mocker):
        mock_dispatch = mocker.patch("src.handlers.message.dispatch_command")
        client.post("/webhook", json=_text_update(ALLOWED_CHAT_ID, "/start"), headers=HEADERS)
        mock_dispatch.assert_called_once_with(ALLOWED_CHAT_ID, "/start")

    def test_photo_calls_handle_photo(self, mocker):
        mock_photo = mocker.patch("src.handlers.message.handle_photo")
        client.post("/webhook", json=_photo_update(ALLOWED_CHAT_ID), headers=HEADERS)
        mock_photo.assert_called_once()
        assert mock_photo.call_args[0][0] == ALLOWED_CHAT_ID

    def test_pdf_calls_handle_pdf(self, mocker):
        mock_pdf = mocker.patch("src.handlers.message.handle_pdf")
        client.post("/webhook", json=_pdf_update(ALLOWED_CHAT_ID), headers=HEADERS)
        mock_pdf.assert_called_once()
        assert mock_pdf.call_args[0][0] == ALLOWED_CHAT_ID

    def test_callback_query_calls_handle_callback(self, mocker):
        mock_cb = mocker.patch("src.handlers.callback.handle_callback", new_callable=mocker.AsyncMock)
        client.post("/webhook", json=_callback_update(ALLOWED_CHAT_ID, "confirm:12345"), headers=HEADERS)
        mock_cb.assert_called_once()

    def test_largest_photo_selected(self):
        update = _photo_update(ALLOWED_CHAT_ID)
        photos = update["message"]["photo"]
        largest = max(photos, key=lambda p: p["file_size"])
        assert largest["file_id"] == "large"


# --- _extract_chat_id ---

class TestExtractChatId:
    def test_from_message(self):
        assert _extract_chat_id({"message": {"chat": {"id": 123}}}) == 123

    def test_from_edited_message(self):
        assert _extract_chat_id({"edited_message": {"chat": {"id": 456}}}) == 456

    def test_from_callback_query(self):
        update = {"callback_query": {"message": {"chat": {"id": 789}}}}
        assert _extract_chat_id(update) == 789

    def test_unknown_returns_none(self):
        assert _extract_chat_id({"unknown": {}}) is None


# --- Health ---

class TestHealth:
    def test_health_ok(self):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
