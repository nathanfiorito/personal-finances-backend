import datetime as _dt
from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from src.v2.domain.entities.category import Category
from src.v2.domain.entities.expense import Expense, ExtractedExpense
from src.v2.domain.ports.category_repository import CategoryRepository, CategoryUpdate
from src.v2.domain.ports.expense_repository import (
    ExpenseFilters,
    ExpenseRepository,
    ExpenseUpdate,
)
from src.v2.domain.ports.llm_port import LLMPort
from src.v2.domain.ports.notifier_port import NotificationButton, NotifierPort
from src.v2.domain.ports.pending_state_port import PendingExpense, PendingStatePort
from src.v2.domain.use_cases.telegram.cancel_expense import (
    CancelExpense,
    CancelExpenseCommand,
)
from src.v2.domain.use_cases.telegram.change_category import (
    ChangeCategory,
    ChangeCategoryCommand,
)
from src.v2.domain.use_cases.telegram.confirm_expense import (
    ConfirmExpense,
    ConfirmExpenseCommand,
)
from src.v2.domain.use_cases.telegram.generate_telegram_report import (
    GenerateTelegramReport,
    GenerateTelegramReportCommand,
)
from src.v2.domain.use_cases.telegram.process_message import (
    ProcessMessage,
    ProcessMessageCommand,
)


# ── Stubs ────────────────────────────────────────────────────────────────────

def _make_expense() -> Expense:
    return Expense(
        id=uuid4(),
        amount=Decimal("50.00"),
        date=_dt.date(2026, 1, 15),
        establishment="Store",
        description=None,
        category_id=1,
        category="Alimentação",
        tax_id=None,
        entry_type="text",
        transaction_type="outcome",
        payment_method="debit",
        confidence=0.9,
        created_at=_dt.datetime(2026, 1, 15, 10, 0),
    )


def _make_extracted() -> ExtractedExpense:
    return ExtractedExpense(
        amount=Decimal("50.00"),
        date=_dt.date(2026, 1, 15),
        establishment="Store",
        entry_type="text",
        transaction_type="outcome",
        confidence=0.9,
    )


class StubExpenseRepository(ExpenseRepository):
    def __init__(self):
        self._saved: list[Expense] = []

    async def save(self, expense: ExtractedExpense, category_id: int) -> Expense:
        e = _make_expense()
        self._saved.append(e)
        return e

    async def get_by_id(self, expense_id: UUID) -> Expense | None:
        return None

    async def list_paginated(self, filters) -> tuple[list[Expense], int]:
        return [], 0

    async def list_by_period(self, start, end, transaction_type=None) -> list[Expense]:
        return self._saved

    async def get_recent(self, limit: int = 3) -> list[Expense]:
        return []

    async def update(self, expense_id, data) -> Expense | None:
        return None

    async def delete(self, expense_id) -> bool:
        return False


class StubCategoryRepository(CategoryRepository):
    async def list_active(self) -> list[str]:
        return ["Alimentação", "Transporte"]

    async def list_all(self) -> list[Category]:
        return [
            Category(id=1, name="Alimentação", is_active=True),
            Category(id=2, name="Transporte", is_active=True),
        ]

    async def create(self, name: str) -> Category:
        return Category(id=3, name=name, is_active=True)

    async def update(self, category_id, data) -> Category | None:
        return None

    async def deactivate(self, category_id) -> bool:
        return False


class StubLLMPort(LLMPort):
    def __init__(self, duplicate_reason: str | None = None):
        self._duplicate_reason = duplicate_reason

    async def extract_from_image(self, image_b64: str) -> ExtractedExpense:
        return _make_extracted()

    async def extract_from_text(self, text: str) -> ExtractedExpense:
        return _make_extracted()

    async def categorize(self, expense, categories) -> str:
        return "Alimentação"

    async def check_duplicate(self, expense, recent) -> str | None:
        return self._duplicate_reason

    async def generate_report(self, expenses, period: str) -> str:
        return "Gastos dentro do normal."


class StubNotifierPort(NotifierPort):
    def __init__(self):
        self.sent_messages: list[dict] = []
        self.edited_messages: list[dict] = []
        self.sent_files: list[dict] = []

    async def send_message(self, chat_id, text, parse_mode=None, buttons=None):
        self.sent_messages.append({"chat_id": chat_id, "text": text, "buttons": buttons})

    async def send_file(self, chat_id, content, filename, caption):
        self.sent_files.append({"chat_id": chat_id, "filename": filename})

    async def answer_callback(self, callback_id, text=None):
        pass

    async def edit_message(self, chat_id, message_id, text, parse_mode=None, buttons=None):
        self.edited_messages.append({"chat_id": chat_id, "text": text})


class StubPendingStatePort(PendingStatePort):
    def __init__(self, initial: PendingExpense | None = None, chat_id: int | None = None):
        self._store: dict[int, PendingExpense] = {}
        if initial and chat_id:
            self._store[chat_id] = initial

    def set(self, chat_id, state):
        self._store[chat_id] = state

    def get(self, chat_id) -> PendingExpense | None:
        s = self._store.get(chat_id)
        if s and s.is_expired():
            self.clear(chat_id)
            return None
        return s

    def update_category(self, chat_id, category, category_id) -> bool:
        s = self.get(chat_id)
        if s is None:
            return False
        s.category = category
        s.category_id = category_id
        return True

    def clear(self, chat_id):
        self._store.pop(chat_id, None)


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_process_message_sends_confirmation_for_text():
    notifier = StubNotifierPort()
    pending = StubPendingStatePort()
    use_case = ProcessMessage(
        llm=StubLLMPort(),
        category_repo=StubCategoryRepository(),
        pending=pending,
        notifier=notifier,
    )
    await use_case.execute(
        ProcessMessageCommand(chat_id=123, entry_type="text", text="gastei 50 no mercado")
    )
    assert len(notifier.sent_messages) == 1
    msg = notifier.sent_messages[0]
    assert msg["chat_id"] == 123
    assert msg["buttons"] is not None  # confirmation keyboard was sent
    assert pending.get(123) is not None  # state stored
    assert "Despesa 🔴" in msg["text"]  # outcome type label shown


@pytest.mark.asyncio
async def test_process_message_sends_confirmation_for_image():
    notifier = StubNotifierPort()
    pending = StubPendingStatePort()
    use_case = ProcessMessage(
        llm=StubLLMPort(),
        category_repo=StubCategoryRepository(),
        pending=pending,
        notifier=notifier,
    )
    await use_case.execute(
        ProcessMessageCommand(chat_id=123, entry_type="image", image_b64="base64data")
    )
    assert len(notifier.sent_messages) == 1
    assert pending.get(123) is not None


@pytest.mark.asyncio
async def test_process_message_shows_income_label_for_income_type():
    """Confirmation message shows 'Receita' for income transactions."""
    class IncomeLLM(StubLLMPort):
        async def extract_from_text(self, text):
            return ExtractedExpense(
                amount=Decimal("1000.00"),
                date=_dt.date(2026, 1, 15),
                establishment="Employer",
                entry_type="text",
                transaction_type="income",
                confidence=0.9,
            )

    notifier = StubNotifierPort()
    use_case = ProcessMessage(
        llm=IncomeLLM(),
        category_repo=StubCategoryRepository(),
        pending=StubPendingStatePort(),
        notifier=notifier,
    )
    await use_case.execute(
        ProcessMessageCommand(chat_id=123, entry_type="text", text="recebi salário")
    )
    assert "Receita 💚" in notifier.sent_messages[0]["text"]


@pytest.mark.asyncio
async def test_confirm_expense_saves_and_notifies():
    extracted = _make_extracted()
    state = PendingExpense(
        extracted=extracted,
        category="Alimentação",
        category_id=1,
        chat_id=123,
        message_id=42,
    )
    repo = StubExpenseRepository()
    notifier = StubNotifierPort()
    pending = StubPendingStatePort(initial=state, chat_id=123)
    use_case = ConfirmExpense(
        repo=repo,
        llm=StubLLMPort(duplicate_reason=None),
        pending=pending,
        notifier=notifier,
    )
    await use_case.execute(ConfirmExpenseCommand(chat_id=123, message_id=42))
    assert len(repo._saved) == 1
    assert pending.get(123) is None  # cleared after save
    assert any("registrada" in m["text"] for m in notifier.sent_messages)


@pytest.mark.asyncio
async def test_confirm_expense_warns_on_duplicate():
    extracted = _make_extracted()
    state = PendingExpense(
        extracted=extracted,
        category="Alimentação",
        category_id=1,
        chat_id=123,
        message_id=42,
    )
    repo = StubExpenseRepository()
    notifier = StubNotifierPort()
    pending = StubPendingStatePort(initial=state, chat_id=123)
    use_case = ConfirmExpense(
        repo=repo,
        llm=StubLLMPort(duplicate_reason="Same store, same amount, yesterday"),
        pending=pending,
        notifier=notifier,
    )
    await use_case.execute(ConfirmExpenseCommand(chat_id=123, message_id=42))
    assert len(repo._saved) == 0  # not saved yet
    assert pending.get(123) is not None  # still pending
    assert any("duplicidade" in m["text"].lower() or "duplicate" in m["text"].lower()
               for m in notifier.sent_messages + notifier.edited_messages)


@pytest.mark.asyncio
async def test_confirm_expense_force_skips_duplicate_check():
    extracted = _make_extracted()
    state = PendingExpense(
        extracted=extracted,
        category="Alimentação",
        category_id=1,
        chat_id=123,
        message_id=42,
    )
    repo = StubExpenseRepository()
    notifier = StubNotifierPort()
    pending = StubPendingStatePort(initial=state, chat_id=123)
    use_case = ConfirmExpense(
        repo=repo,
        llm=StubLLMPort(duplicate_reason="would be a duplicate"),
        pending=pending,
        notifier=notifier,
    )
    await use_case.execute(
        ConfirmExpenseCommand(chat_id=123, message_id=42, skip_duplicate_check=True)
    )
    assert len(repo._saved) == 1


@pytest.mark.asyncio
async def test_cancel_expense_clears_pending_and_notifies():
    state = PendingExpense(
        extracted=_make_extracted(),
        category="Alimentação",
        category_id=1,
        chat_id=123,
        message_id=42,
    )
    notifier = StubNotifierPort()
    pending = StubPendingStatePort(initial=state, chat_id=123)
    use_case = CancelExpense(pending=pending, notifier=notifier)
    await use_case.execute(CancelExpenseCommand(chat_id=123, message_id=42))
    assert pending.get(123) is None
    assert len(notifier.edited_messages) == 1


@pytest.mark.asyncio
async def test_change_category_updates_pending_and_resends_confirmation():
    state = PendingExpense(
        extracted=_make_extracted(),
        category="Alimentação",
        category_id=1,
        chat_id=123,
        message_id=42,
    )
    notifier = StubNotifierPort()
    pending = StubPendingStatePort(initial=state, chat_id=123)
    use_case = ChangeCategory(pending=pending, notifier=notifier)
    await use_case.execute(
        ChangeCategoryCommand(
            chat_id=123,
            message_id=42,
            new_category="Transporte",
            new_category_id=2,
        )
    )
    updated = pending.get(123)
    assert updated is not None
    assert updated.category == "Transporte"
    assert len(notifier.edited_messages) == 1


@pytest.mark.asyncio
async def test_generate_telegram_report_sends_message():
    notifier = StubNotifierPort()
    repo = StubExpenseRepository()
    use_case = GenerateTelegramReport(repo=repo, llm=StubLLMPort(), notifier=notifier)
    await use_case.execute(
        GenerateTelegramReportCommand(
            chat_id=123,
            period_label="Janeiro 2026",
            start=_dt.date(2026, 1, 1),
            end=_dt.date(2026, 1, 31),
        )
    )
    assert len(notifier.sent_messages) == 1
    assert "123" not in notifier.sent_messages[0]["text"]  # shouldn't leak chat_id
