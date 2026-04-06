from datetime import datetime, timedelta

from src.models.expense import ExtractedExpense

_TTL_MINUTES = 10
_store: dict[int, "_PendingExpense"] = {}


class _PendingExpense:
    def __init__(self, extracted: ExtractedExpense, categoria: str, message_id: int):
        self.extracted = extracted
        self.categoria = categoria
        self.message_id = message_id
        self.created_at = datetime.now()

    def is_expired(self) -> bool:
        return datetime.now() - self.created_at > timedelta(minutes=_TTL_MINUTES)


def save(chat_id: int, extracted: ExtractedExpense, categoria: str, message_id: int) -> None:
    _store[chat_id] = _PendingExpense(extracted, categoria, message_id)


def get(chat_id: int) -> _PendingExpense | None:
    pending = _store.get(chat_id)
    if pending is None:
        return None
    if pending.is_expired():
        delete(chat_id)
        return None
    return pending


def update_categoria(chat_id: int, categoria: str) -> bool:
    pending = get(chat_id)
    if pending is None:
        return False
    pending.categoria = categoria
    return True


def delete(chat_id: int) -> None:
    _store.pop(chat_id, None)
