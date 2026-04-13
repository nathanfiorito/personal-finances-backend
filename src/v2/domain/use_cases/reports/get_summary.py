from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Literal

from src.v2.domain.ports.expense_repository import ExpenseRepository


@dataclass
class SummaryItem:
    category: str
    total: Decimal


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
        for expense in expenses:
            totals[expense.category] = (
                totals.get(expense.category, Decimal("0")) + expense.amount
            )
        return [
            SummaryItem(category=cat, total=total)
            for cat, total in sorted(totals.items())
        ]
