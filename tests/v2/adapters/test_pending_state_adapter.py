import time
from decimal import Decimal
from unittest.mock import patch

import pytest

from src.v2.adapters.secondary.memory.pending_state_adapter import InMemoryPendingStateAdapter
from src.v2.domain.entities.expense import ExtractedExpense
from src.v2.domain.ports.pending_state_port import PendingExpense


def _make_pending(chat_id: int = 1) -> PendingExpense:
    extracted = ExtractedExpense(
        amount=Decimal("99.90"),
        entry_type="text",
    )
    return PendingExpense(
        extracted=extracted,
        category="Alimentação",
        category_id=1,
        chat_id=chat_id,
    )


@pytest.fixture
def adapter():
    return InMemoryPendingStateAdapter()


def test_set_and_get_returns_state(adapter):
    state = _make_pending(chat_id=1)
    adapter.set(1, state)
    result = adapter.get(1)
    assert result is state


def test_get_missing_key_returns_none(adapter):
    assert adapter.get(999) is None


def test_clear_removes_state(adapter):
    adapter.set(1, _make_pending(chat_id=1))
    adapter.clear(1)
    assert adapter.get(1) is None


def test_clear_nonexistent_key_is_noop(adapter):
    adapter.clear(999)  # should not raise


def test_expired_state_returns_none(adapter):
    state = _make_pending(chat_id=1)
    with patch.object(state, "is_expired", return_value=True):
        adapter.set(1, state)
        result = adapter.get(1)
    assert result is None


def test_update_category_modifies_state(adapter):
    adapter.set(1, _make_pending(chat_id=1))
    updated = adapter.update_category(1, "Saúde", category_id=5)
    assert updated is True
    state = adapter.get(1)
    assert state.category == "Saúde"
    assert state.category_id == 5


def test_update_category_missing_key_returns_false(adapter):
    result = adapter.update_category(999, "Saúde", category_id=5)
    assert result is False
