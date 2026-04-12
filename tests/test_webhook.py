import pytest
from fastapi.testclient import TestClient

from src.main import app, _extract_chat_id

client = TestClient(app)

VALID_SECRET = "test-secret"
ALLOWED_CHAT_ID = 12345
# Use a Telegram IP from the 149.154.160.0/20 range
TELEGRAM_IP = "149.154.167.1"
HEADERS = {"X-Telegram-Bot-Api-Secret-Token": VALID_SECRET}


@pytest.fixture(autouse=True)
def patch_settings(monkeypatch):
    from types import SimpleNamespace
    import src.main as main_module
    import src.config.settings as settings_module

    monkeypatch.setattr(settings_module.settings, "telegram_webhook_secret", VALID_SECRET)
    monkeypatch.setattr(settings_module.settings, "telegram_allowed_chat_id", ALLOWED_CHAT_ID)
    monkeypatch.setattr(main_module.settings, "telegram_webhook_secret", VALID_SECRET)
    monkeypatch.setattr(main_module.settings, "telegram_allowed_chat_id", ALLOWED_CHAT_ID)
    # TestClient doesn't run lifespan; wire a stub so the webhook can read use_cases
    app.state.use_cases = SimpleNamespace()


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
        mocker.patch("src.v2.adapters.primary.telegram.webhook.handle_update")
        response = _post_webhook(_text_update(ALLOWED_CHAT_ID, "oi"))
        assert response.status_code == 200

    def test_unauthorized_chat_id_ignored(self, mocker):
        mock_handle = mocker.patch("src.v2.adapters.primary.telegram.webhook.handle_update")
        response = _post_webhook(_text_update(99999, "oi"))
        assert response.status_code == 200
        mock_handle.assert_not_called()

    def test_authorized_chat_id_processed(self, mocker):
        mock_handle = mocker.patch("src.v2.adapters.primary.telegram.webhook.handle_update")
        _post_webhook(_text_update(ALLOWED_CHAT_ID, "oi"))
        mock_handle.assert_called_once()

    def test_any_ip_accepted_with_valid_secret(self, mocker):
        # IP validation was removed — only the secret token is checked
        mocker.patch("src.v2.adapters.primary.telegram.webhook.handle_update")
        response = _post_webhook(
            _text_update(ALLOWED_CHAT_ID, "oi"),
            client_ip="1.2.3.4",
        )
        assert response.status_code == 200


# --- CORS ---

class TestCORS:
    @pytest.mark.parametrize("origin", [
        "https://nathanfiorito.com.br",
        "https://www.nathanfiorito.com.br",
        "https://app.nathanfiorito.com.br",
        "https://api.nathanfiorito.com.br",
        "https://personal-finances.nathanfiorito.com.br",
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


# --- Roteamento (v2) ---

class TestRouting:
    def test_text_message_routes_to_handle_message(self, mocker):
        mock_msg = mocker.patch(
            "src.v2.adapters.primary.telegram.webhook.handle_message",
            new_callable=mocker.AsyncMock,
        )
        _post_webhook(_text_update(ALLOWED_CHAT_ID, "gastei 50 no mercado"))
        mock_msg.assert_called_once()

    def test_command_routes_to_handle_command(self, mocker):
        mock_cmd = mocker.patch(
            "src.v2.adapters.primary.telegram.webhook.handle_command",
            new_callable=mocker.AsyncMock,
        )
        _post_webhook(_text_update(ALLOWED_CHAT_ID, "/start"))
        mock_cmd.assert_called_once()

    def test_photo_routes_to_handle_message(self, mocker):
        mock_msg = mocker.patch(
            "src.v2.adapters.primary.telegram.webhook.handle_message",
            new_callable=mocker.AsyncMock,
        )
        _post_webhook(_photo_update(ALLOWED_CHAT_ID))
        mock_msg.assert_called_once()

    def test_pdf_routes_to_handle_message(self, mocker):
        mock_msg = mocker.patch(
            "src.v2.adapters.primary.telegram.webhook.handle_message",
            new_callable=mocker.AsyncMock,
        )
        _post_webhook(_pdf_update(ALLOWED_CHAT_ID))
        mock_msg.assert_called_once()

    def test_callback_query_routes_to_handle_callback(self, mocker):
        mock_cb = mocker.patch(
            "src.v2.adapters.primary.telegram.webhook.handle_callback",
            new_callable=mocker.AsyncMock,
        )
        _post_webhook(_callback_update(ALLOWED_CHAT_ID, "confirm"))
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
