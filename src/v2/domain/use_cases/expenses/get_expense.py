from dataclasses import dataclass
from uuid import UUID

from src.v2.domain.entities.expense import Expense
from src.v2.domain.exceptions import ExpenseNotFoundError
from src.v2.domain.ports.expense_repository import ExpenseRepository


@dataclass
class GetExpenseQuery:
    expense_id: UUID


class GetExpense:
    def __init__(self, repo: ExpenseRepository) -> None:
        self._repo = repo

    async def execute(self, query: GetExpenseQuery) -> Expense:
        expense = await self._repo.get_by_id(query.expense_id)
        if expense is None:
            raise ExpenseNotFoundError(f"Expense {query.expense_id} not found")
        return expense
