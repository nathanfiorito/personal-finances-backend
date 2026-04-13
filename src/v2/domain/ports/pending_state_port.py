import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from src.v2.domain.entities.expense import ExtractedExpense

_TTL_SECONDS = 600  # 10 minutes


@dataclass
class PendingExpense:
    extracted: ExtractedExpense
    category: str          # display name shown in confirmation message
    category_id: int       # used by ConfirmExpense to persist
    chat_id: int
    message_id: int | None = None
    expires_at: float = field(
        default_factory=lambda: time.monotonic() + _TTL_SECONDS
    )

    def is_expired(self) -> bool:
        return time.monotonic() > self.expires_at


class PendingStatePort(ABC):
    @abstractmethod
    def set(self, chat_id: int, state: PendingExpense) -> None: ...

    @abstractmethod
    def get(self, chat_id: int) -> PendingExpense | None: ...

    @abstractmethod
    def update_category(
        self, chat_id: int, category: str, category_id: int
    ) -> bool:
        """Update category on an existing pending state. Returns False if expired/missing."""
        ...

    @abstractmethod
    def clear(self, chat_id: int) -> None: ...
