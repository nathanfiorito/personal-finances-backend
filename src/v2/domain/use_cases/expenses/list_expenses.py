from dataclasses import dataclass
from datetime import date
from typing import Literal, Optional, Tuple

from src.v2.domain.entities.expense import Expense
from src.v2.domain.ports.expense_repository import ExpenseFilters, ExpenseRepository


@dataclass
class ListExpensesQuery:
    start: Optional[date] = None
    end: Optional[date] = None
    category_id: Optional[int] = None
    transaction_type: Optional[Literal["income", "outcome"]] = None
    page: int = 1
    page_size: int = 20


class ListExpenses:
    def __init__(self, repo: ExpenseRepository) -> None:
        self._repo = repo

    async def execute(self, query: ListExpensesQuery) -> Tuple[list[Expense], int]:
        filters = ExpenseFilters(
            start=query.start,
            end=query.end,
            category_id=query.category_id,
            transaction_type=query.transaction_type,
            page=query.page,
            page_size=min(query.page_size, 100),
        )
        return await self._repo.list_paginated(filters)
