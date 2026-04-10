import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

from src.models import pending as pending_store
from src.models.expense import Expense, ExtractedExpense
from src.handlers.callback import handle_callback


CHAT_ID = 12345
MESSAGE_ID = 99


def _expense() -> ExtractedExpense:
    return ExtractedExpense(
        amount=Decimal("45.90"),
        date=date(2024, 1, 15),
        establishment="Supermercado Extra",
        description="Compras",
        entry_type="texto",
        confidence=0.9,
    )


def _saved_expense() -> Expense:
    return Expense(
        id="550e8400-e29b-41d4-a716-446655440000",
        amount=Decimal("45.90"),
        date=date(2024, 1, 14),
        establishment="Supermercado Extra",
        description="Compras",
        category="Alimentação",
        tax_id=None,
        entry_type="texto",
        confidence=0.9,
        created_at=datetime(2024, 1, 14, 10, 0, 0),
    )


def _callback(data: str) -> dict:
    return {
        "id": "cq1",
        "from": {"id": CHAT_ID},
        "message": {"message_id": MESSAGE_ID, "chat": {"id": CHAT_ID}},
        "data": data,
    }


@pytest.fixture(autouse=True)
def clean_store():
    pending_store.delete(CHAT_ID)
    yield
    pending_store.delete(CHAT_ID)


@pytest.fixture
def with_pending():
    pending_store.save(CHAT_ID, _expense(), "Alimentação", MESSAGE_ID)


@pytest.fixture
def mock_no_duplicate(mocker):
    """Default: no duplicates found."""
    mocker.patch("src.services.database.get_recent_expenses", new_callable=AsyncMock, return_value=[])
    mocker.patch("src.agents.duplicate_checker.check_duplicate", new_callable=AsyncMock, return_value=None)


# --- Confirm (caminho feliz) ---

class TestConfirm:
    @pytest.mark.asyncio
    async def test_saves_expense_and_sends_confirmation(self, with_pending, mock_no_duplicate, mocker):
        mock_save = mocker.patch("src.services.database.save_expense", new_callable=AsyncMock)
        mocker.patch("src.services.telegram.edit_message", new_callable=AsyncMock)
        mock_send = mocker.patch("src.services.telegram.send_message", new_callable=AsyncMock)
        mocker.patch("src.services.telegram.answer_callback", new_callable=AsyncMock)

        await handle_callback(_callback("confirm"))

        mock_save.assert_called_once_with(pytest.approx(_expense(), abs=0), "Alimentação")
        mock_send.assert_called_once()
        assert "45,90" in mock_send.call_args[0][1]
        assert "Alimentação" in mock_send.call_args[0][1]

    @pytest.mark.asyncio
    async def test_removes_from_store_after_confirm(self, with_pending, mock_no_duplicate, mocker):
        mocker.patch("src.services.database.save_expense", new_callable=AsyncMock)
        mocker.patch("src.services.telegram.edit_message", new_callable=AsyncMock)
        mocker.patch("src.services.telegram.send_message", new_callable=AsyncMock)
        mocker.patch("src.services.telegram.answer_callback", new_callable=AsyncMock)

        await handle_callback(_callback("confirm"))

        assert pending_store.get(CHAT_ID) is None

    @pytest.mark.asyncio
    async def test_expired_pending_shows_message(self, mocker):
        mock_answer = mocker.patch("src.services.telegram.answer_callback", new_callable=AsyncMock)
        mocker.patch("src.services.telegram.edit_message", new_callable=AsyncMock)

        await handle_callback(_callback("confirm"))

        mock_answer.assert_called_once()
        assert "expirada" in mock_answer.call_args[0][1].lower()

    @pytest.mark.asyncio
    async def test_db_error_sends_error_message(self, with_pending, mock_no_duplicate, mocker):
        mocker.patch("src.services.database.save_expense", new_callable=AsyncMock, side_effect=Exception("DB error"))
        mocker.patch("src.services.telegram.edit_message", new_callable=AsyncMock)
        mock_send = mocker.patch("src.services.telegram.send_message", new_callable=AsyncMock)
        mocker.patch("src.services.telegram.answer_callback", new_callable=AsyncMock)

        await handle_callback(_callback("confirm"))

        assert "Erro" in mock_send.call_args[0][1]
        assert pending_store.get(CHAT_ID) is None


# --- Duplicate detection ---

class TestDuplicateDetection:
    @pytest.mark.asyncio
    async def test_duplicate_detected_shows_warning_keyboard(self, with_pending, mocker):
        mocker.patch("src.services.database.get_recent_expenses", new_callable=AsyncMock, return_value=[_saved_expense()])
        mocker.patch("src.agents.duplicate_checker.check_duplicate", new_callable=AsyncMock,
                     return_value="Mesmo valor e estabelecimento registrados ontem")
        mock_edit = mocker.patch("src.services.telegram.edit_message", new_callable=AsyncMock)
        mocker.patch("src.services.telegram.answer_callback", new_callable=AsyncMock)

        await handle_callback(_callback("confirm"))

        call_kwargs = mock_edit.call_args[1]
        keyboard = call_kwargs.get("reply_markup", {})
        buttons = [btn["callback_data"] for row in keyboard["inline_keyboard"] for btn in row]
        assert "force_confirm" in buttons
        assert "cancel" in buttons

    @pytest.mark.asyncio
    async def test_duplicate_detected_does_not_save(self, with_pending, mocker):
        mocker.patch("src.services.database.get_recent_expenses", new_callable=AsyncMock, return_value=[_saved_expense()])
        mocker.patch("src.agents.duplicate_checker.check_duplicate", new_callable=AsyncMock,
                     return_value="Mesmo valor e estabelecimento registrados ontem")
        mock_save = mocker.patch("src.services.database.save_expense", new_callable=AsyncMock)
        mocker.patch("src.services.telegram.edit_message", new_callable=AsyncMock)
        mocker.patch("src.services.telegram.answer_callback", new_callable=AsyncMock)

        await handle_callback(_callback("confirm"))

        mock_save.assert_not_called()

    @pytest.mark.asyncio
    async def test_duplicate_detected_keeps_pending(self, with_pending, mocker):
        mocker.patch("src.services.database.get_recent_expenses", new_callable=AsyncMock, return_value=[_saved_expense()])
        mocker.patch("src.agents.duplicate_checker.check_duplicate", new_callable=AsyncMock,
                     return_value="Possível duplicata")
        mocker.patch("src.services.telegram.edit_message", new_callable=AsyncMock)
        mocker.patch("src.services.telegram.answer_callback", new_callable=AsyncMock)

        await handle_callback(_callback("confirm"))

        assert pending_store.get(CHAT_ID) is not None

    @pytest.mark.asyncio
    async def test_duplicate_warning_shows_reason(self, with_pending, mocker):
        reason = "Mesmo valor e estabelecimento registrados ontem"
        mocker.patch("src.services.database.get_recent_expenses", new_callable=AsyncMock, return_value=[_saved_expense()])
        mocker.patch("src.agents.duplicate_checker.check_duplicate", new_callable=AsyncMock, return_value=reason)
        mock_edit = mocker.patch("src.services.telegram.edit_message", new_callable=AsyncMock)
        mocker.patch("src.services.telegram.answer_callback", new_callable=AsyncMock)

        await handle_callback(_callback("confirm"))

        edited_text = mock_edit.call_args[0][2]
        assert reason in edited_text

    @pytest.mark.asyncio
    async def test_llm_failure_does_not_block_save(self, with_pending, mocker):
        mocker.patch("src.services.database.get_recent_expenses", new_callable=AsyncMock, side_effect=Exception("DB error"))
        mock_save = mocker.patch("src.services.database.save_expense", new_callable=AsyncMock)
        mocker.patch("src.services.telegram.edit_message", new_callable=AsyncMock)
        mocker.patch("src.services.telegram.send_message", new_callable=AsyncMock)
        mocker.patch("src.services.telegram.answer_callback", new_callable=AsyncMock)

        await handle_callback(_callback("confirm"))

        mock_save.assert_called_once()


# --- Force confirm ---

class TestForceConfirm:
    @pytest.mark.asyncio
    async def test_saves_without_duplicate_check(self, with_pending, mocker):
        mock_save = mocker.patch("src.services.database.save_expense", new_callable=AsyncMock)
        mock_check = mocker.patch("src.agents.duplicate_checker.check_duplicate", new_callable=AsyncMock)
        mocker.patch("src.services.telegram.edit_message", new_callable=AsyncMock)
        mocker.patch("src.services.telegram.send_message", new_callable=AsyncMock)
        mocker.patch("src.services.telegram.answer_callback", new_callable=AsyncMock)

        await handle_callback(_callback("force_confirm"))

        mock_save.assert_called_once()
        mock_check.assert_not_called()

    @pytest.mark.asyncio
    async def test_removes_from_store(self, with_pending, mocker):
        mocker.patch("src.services.database.save_expense", new_callable=AsyncMock)
        mocker.patch("src.services.telegram.edit_message", new_callable=AsyncMock)
        mocker.patch("src.services.telegram.send_message", new_callable=AsyncMock)
        mocker.patch("src.services.telegram.answer_callback", new_callable=AsyncMock)

        await handle_callback(_callback("force_confirm"))

        assert pending_store.get(CHAT_ID) is None

    @pytest.mark.asyncio
    async def test_expired_shows_message(self, mocker):
        mock_answer = mocker.patch("src.services.telegram.answer_callback", new_callable=AsyncMock)
        mocker.patch("src.services.telegram.edit_message", new_callable=AsyncMock)

        await handle_callback(_callback("force_confirm"))

        assert "expirada" in mock_answer.call_args[0][1].lower()


# --- Cancel ---

class TestCancel:
    @pytest.mark.asyncio
    async def test_removes_from_store(self, with_pending, mocker):
        mocker.patch("src.services.telegram.answer_callback", new_callable=AsyncMock)
        mocker.patch("src.services.telegram.edit_message", new_callable=AsyncMock)

        await handle_callback(_callback("cancel"))

        assert pending_store.get(CHAT_ID) is None

    @pytest.mark.asyncio
    async def test_edits_message_to_cancelled(self, with_pending, mocker):
        mocker.patch("src.services.telegram.answer_callback", new_callable=AsyncMock)
        mock_edit = mocker.patch("src.services.telegram.edit_message", new_callable=AsyncMock)

        await handle_callback(_callback("cancel"))

        assert "cancelada" in mock_edit.call_args[0][2].lower()


# --- Edit category ---

class TestEditCategory:
    @pytest.mark.asyncio
    async def test_sends_category_keyboard(self, with_pending, mocker):
        mocker.patch("src.services.telegram.answer_callback", new_callable=AsyncMock)
        mock_edit = mocker.patch("src.services.telegram.edit_message", new_callable=AsyncMock)

        await handle_callback(_callback("edit_category"))

        mock_edit.assert_called_once()
        call_kwargs = mock_edit.call_args[1]
        assert "inline_keyboard" in call_kwargs.get("reply_markup", {})

    @pytest.mark.asyncio
    async def test_set_category_updates_store(self, with_pending, mocker):
        mocker.patch("src.services.telegram.answer_callback", new_callable=AsyncMock)
        mocker.patch("src.services.telegram.edit_message", new_callable=AsyncMock)

        await handle_callback(_callback("set_category:Transporte"))

        updated = pending_store.get(CHAT_ID)
        assert updated.category == "Transporte"

    @pytest.mark.asyncio
    async def test_set_category_reshow_confirmation(self, with_pending, mocker):
        mocker.patch("src.services.telegram.answer_callback", new_callable=AsyncMock)
        mock_edit = mocker.patch("src.services.telegram.edit_message", new_callable=AsyncMock)

        await handle_callback(_callback("set_category:Transporte"))

        call_kwargs = mock_edit.call_args[1]
        keyboard = call_kwargs.get("reply_markup", {})
        assert len(keyboard["inline_keyboard"][0]) == 3


# --- Pending store ---

class TestPendingStore:
    def test_get_returns_none_for_expired(self):
        pending_store.save(CHAT_ID, _expense(), "Alimentação", MESSAGE_ID)
        entry = pending_store._store[CHAT_ID]
        entry.created_at = datetime.now() - timedelta(minutes=11)

        assert pending_store.get(CHAT_ID) is None
        assert CHAT_ID not in pending_store._store

    def test_update_category(self):
        pending_store.save(CHAT_ID, _expense(), "Alimentação", MESSAGE_ID)
        result = pending_store.update_category(CHAT_ID, "Saúde")
        assert result is True
        assert pending_store.get(CHAT_ID).category == "Saúde"

    def test_update_category_missing_returns_false(self):
        result = pending_store.update_category(CHAT_ID, "Saúde")
        assert result is False
