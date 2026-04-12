from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Literal
from uuid import UUID

from src.v2.domain.entities.expense import Expense
from src.v2.domain.exceptions import ExpenseNotFoundError
from src.v2.domain.ports.expense_repository import ExpenseRepository, ExpenseUpdate


@dataclass
class UpdateExpenseCommand:
    expense_id: UUID
    amount: Decimal | None = None
    date: date | None = None
    establishment: str | None = None
    description: str | None = None
    category_id: int | None = None
    tax_id: str | None = None
    entry_type: Literal["image", "text", "pdf"] | None = None
    transaction_type: Literal["income", "outcome"] | None = None


class UpdateExpense:
    def __init__(self, repo: ExpenseRepository) -> None:
        self._repo = repo

    async def execute(self, cmd: UpdateExpenseCommand) -> Expense:
        data = ExpenseUpdate(
            amount=cmd.amount,
            date=cmd.date,
            establishment=cmd.establishment,
            description=cmd.description,
            category_id=cmd.category_id,
            tax_id=cmd.tax_id,
            entry_type=cmd.entry_type,
            transaction_type=cmd.transaction_type,
        )
        expense = await self._repo.update(cmd.expense_id, data)
        if expense is None:
            raise ExpenseNotFoundError(f"Expense {cmd.expense_id} not found")
        return expense
