from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Literal

from src.v2.domain.ports.expense_repository import ExpenseRepository


@dataclass
class MonthlyByCategoryItem:
    category: str
    total: Decimal


@dataclass
class MonthlyItem:
    month: int
    total: Decimal
    by_category: list[MonthlyByCategoryItem]


@dataclass
class GetMonthlyQuery:
    year: int
    transaction_type: Literal["income", "expense"] | None = None


class GetMonthly:
    def __init__(self, repo: ExpenseRepository) -> None:
        self._repo = repo

    async def execute(self, query: GetMonthlyQuery) -> list[MonthlyItem]:
        expenses = await self._repo.list_by_period(
            date(query.year, 1, 1),
            date(query.year, 12, 31),
            query.transaction_type,
        )
        by_month: dict[int, dict[str, Decimal]] = {}
        for expense in expenses:
            m = expense.date.month
            if m not in by_month:
                by_month[m] = {}
            by_month[m][expense.category] = (
                by_month[m].get(expense.category, Decimal("0")) + expense.amount
            )
        return [
            MonthlyItem(
                month=month,
                total=sum(cats.values(), Decimal("0")),
                by_category=[
                    MonthlyByCategoryItem(category=cat, total=total)
                    for cat, total in sorted(cats.items())
                ],
            )
            for month, cats in sorted(by_month.items())
        ]
