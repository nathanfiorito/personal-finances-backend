from src.v2.domain.ports.pending_state_port import PendingExpense, PendingStatePort


class InMemoryPendingStateAdapter(PendingStatePort):
    """Thread-unsafe in-memory store for pending expenses.

    Suitable for single-process deployments (Render free tier runs one worker).
    TTL is enforced lazily on `get()`.
    """

    def __init__(self) -> None:
        self._store: dict[int, PendingExpense] = {}

    def set(self, chat_id: int, state: PendingExpense) -> None:
        self._store[chat_id] = state

    def get(self, chat_id: int) -> PendingExpense | None:
        state = self._store.get(chat_id)
        if state is None:
            return None
        if state.is_expired():
            self.clear(chat_id)
            return None
        return state

    def update_category(
        self, chat_id: int, category: str, category_id: int
    ) -> bool:
        state = self.get(chat_id)
        if state is None:
            return False
        state.category = category
        state.category_id = category_id
        return True

    def clear(self, chat_id: int) -> None:
        self._store.pop(chat_id, None)
