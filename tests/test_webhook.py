import pytest
from fastapi.testclient import TestClient

from src.main import app, _extract_chat_id, _is_telegram_ip

client = TestClient(app)

VALID_SECRET = "test-secret"
ALLOWED_CHAT_ID = 12345
# Use a Telegram IP from the 149.154.160.0/20 range
TELEGRAM_IP = "149.154.167.1"
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

def _post_webhook(json, headers=HEADERS, client_ip=TELEGRAM_IP):
    """Send a POST to /webhook with a simulated source IP via CF-Connecting-IP."""
    all_headers = {**headers, "CF-Connecting-IP": client_ip}
    return client.post("/webhook", json=json, headers=all_headers)


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
        response = client.post(
            "/webhook",
            json=_text_update(ALLOWED_CHAT_ID, "oi"),
            headers={"CF-Connecting-IP": TELEGRAM_IP},
        )
        assert response.status_code == 403

    def test_wrong_secret_returns_403(self):
        response = _post_webhook(
            _text_update(ALLOWED_CHAT_ID, "oi"),
            headers={"X-Telegram-Bot-Api-Secret-Token": "wrong"},
        )
        assert response.status_code == 403

    def test_valid_secret_returns_200(self, mocker):
        mocker.patch("src.main.handle_update")
        response = _post_webhook(_text_update(ALLOWED_CHAT_ID, "oi"))
        assert response.status_code == 200

    def test_unauthorized_chat_id_ignored(self, mocker):
        mock_handle = mocker.patch("src.main.handle_update")
        response = _post_webhook(_text_update(99999, "oi"))
        assert response.status_code == 200
        mock_handle.assert_not_called()

    def test_authorized_chat_id_processed(self, mocker):
        mock_handle = mocker.patch("src.main.handle_update")
        _post_webhook(_text_update(ALLOWED_CHAT_ID, "oi"))
        mock_handle.assert_called_once()

    def test_non_telegram_ip_returns_403(self, mocker):
        mocker.patch("src.main.handle_update")
        response = _post_webhook(
            _text_update(ALLOWED_CHAT_ID, "oi"),
            client_ip="1.2.3.4",
        )
        assert response.status_code == 403

    def test_telegram_ip_range_1_accepted(self, mocker):
        mocker.patch("src.main.handle_update")
        response = _post_webhook(
            _text_update(ALLOWED_CHAT_ID, "oi"),
            client_ip="149.154.175.255",
        )
        assert response.status_code == 200

    def test_telegram_ip_range_2_accepted(self, mocker):
        mocker.patch("src.main.handle_update")
        response = _post_webhook(
            _text_update(ALLOWED_CHAT_ID, "oi"),
            client_ip="91.108.4.1",
        )
        assert response.status_code == 200


# --- IP Validation ---

class TestTelegramIP:
    def test_telegram_ip_in_range_1(self):
        assert _is_telegram_ip("149.154.167.220") is True

    def test_telegram_ip_in_range_2(self):
        assert _is_telegram_ip("91.108.5.100") is True

    def test_non_telegram_ip(self):
        assert _is_telegram_ip("8.8.8.8") is False

    def test_localhost_not_telegram(self):
        assert _is_telegram_ip("127.0.0.1") is False

    def test_invalid_ip_returns_false(self):
        assert _is_telegram_ip("not-an-ip") is False


# --- CORS ---

class TestCORS:
    @pytest.mark.parametrize("origin", [
        "https://nathanfiorito.com.br",
        "https://www.nathanfiorito.com.br",
        "https://app.nathanfiorito.com.br",
        "https://api.nathanfiorito.com.br",
        "https://finbot.nathanfiorito.com.br",
    ])
    def test_cors_allowed_subdomains(self, origin):
        response = client.options(
            "/health",
            headers={"Origin": origin, "Access-Control-Request-Method": "GET"},
        )
        assert response.headers.get("access-control-allow-origin") == origin

    @pytest.mark.parametrize("origin", [
        "https://evil.com",
        "https://nathanfiorito.com.br.evil.com",
        "https://fakenathafiorito.com.br",
        "http://nathanfiorito.com.br",
    ])
    def test_cors_rejected_origins(self, origin):
        response = client.options(
            "/health",
            headers={"Origin": origin, "Access-Control-Request-Method": "GET"},
        )
        assert response.headers.get("access-control-allow-origin") is None


# --- Roteamento ---

class TestRouting:
    @pytest.fixture(autouse=True)
    def mock_telegram(self, mocker):
        mocker.patch("src.handlers.message.telegram.send_message")
        mocker.patch("src.handlers.message.telegram.answer_callback")

    def test_text_message_calls_handle_text(self, mocker):
        mock_text = mocker.patch("src.handlers.message.handle_text")
        _post_webhook(_text_update(ALLOWED_CHAT_ID, "gastei 50 no mercado"))
        mock_text.assert_called_once_with(ALLOWED_CHAT_ID, "gastei 50 no mercado")

    def test_command_calls_dispatch(self, mocker):
        mock_dispatch = mocker.patch("src.handlers.message.dispatch_command")
        _post_webhook(_text_update(ALLOWED_CHAT_ID, "/start"))
        mock_dispatch.assert_called_once_with(ALLOWED_CHAT_ID, "/start")

    def test_photo_calls_handle_photo(self, mocker):
        mock_photo = mocker.patch("src.handlers.message.handle_photo")
        _post_webhook(_photo_update(ALLOWED_CHAT_ID))
        mock_photo.assert_called_once()
        assert mock_photo.call_args[0][0] == ALLOWED_CHAT_ID

    def test_pdf_calls_handle_pdf(self, mocker):
        mock_pdf = mocker.patch("src.handlers.message.handle_pdf")
        _post_webhook(_pdf_update(ALLOWED_CHAT_ID))
        mock_pdf.assert_called_once()
        assert mock_pdf.call_args[0][0] == ALLOWED_CHAT_ID

    def test_callback_query_calls_handle_callback(self, mocker):
        mock_cb = mocker.patch("src.handlers.callback.handle_callback", new_callable=mocker.AsyncMock)
        _post_webhook(_callback_update(ALLOWED_CHAT_ID, "confirm:12345"))
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
