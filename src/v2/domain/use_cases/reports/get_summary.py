from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Literal

from src.v2.domain.ports.expense_repository import ExpenseRepository


@dataclass
class SummaryItem:
    category: str
    total: Decimal
    count: int = 0


@dataclass
class GetSummaryQuery:
    start: date
    end: date
    transaction_type: Literal["income", "expense"] | None = None


class GetSummary:
    def __init__(self, repo: ExpenseRepository) -> None:
        self._repo = repo

    async def execute(self, query: GetSummaryQuery) -> list[SummaryItem]:
        expenses = await self._repo.list_by_period(
            query.start, query.end, query.transaction_type
        )
        totals: dict[str, Decimal] = {}
        counts: dict[str, int] = {}
        for expense in expenses:
            totals[expense.category] = (
                totals.get(expense.category, Decimal("0")) + expense.amount
            )
            counts[expense.category] = counts.get(expense.category, 0) + 1
        return [
            SummaryItem(category=cat, total=totals[cat], count=counts[cat])
            for cat in sorted(totals)
        ]
