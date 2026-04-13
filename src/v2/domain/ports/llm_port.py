from abc import ABC, abstractmethod

from src.v2.domain.entities.expense import Expense, ExtractedExpense


class LLMPort(ABC):
    @abstractmethod
    async def extract_from_image(self, image_b64: str) -> ExtractedExpense: ...

    @abstractmethod
    async def extract_from_text(self, text: str) -> ExtractedExpense: ...

    @abstractmethod
    async def categorize(
        self, expense: ExtractedExpense, categories: list[str]
    ) -> str: ...

    @abstractmethod
    async def check_duplicate(
        self, expense: ExtractedExpense, recent: list[Expense]
    ) -> str | None:
        """Return a human-readable reason string if duplicate, or None if not."""
        ...

    @abstractmethod
    async def generate_report(
        self, expenses: list[Expense], period: str
    ) -> str: ...
