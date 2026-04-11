from dataclasses import dataclass
from uuid import UUID

from src.v2.domain.exceptions import ExpenseNotFoundError
from src.v2.domain.ports.expense_repository import ExpenseRepository


@dataclass
class DeleteExpenseCommand:
    expense_id: UUID


class DeleteExpense:
    def __init__(self, repo: ExpenseRepository) -> None:
        self._repo = repo

    async def execute(self, cmd: DeleteExpenseCommand) -> None:
        deleted = await self._repo.delete(cmd.expense_id)
        if not deleted:
            raise ExpenseNotFoundError(f"Expense {cmd.expense_id} not found")
