from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Literal

from src.v2.domain.entities.expense import Expense, ExtractedExpense
from src.v2.domain.ports.expense_repository import ExpenseRepository


@dataclass
class CreateExpenseCommand:
    amount: Decimal
    date: date
    category_id: int
    entry_type: Literal["image", "text", "pdf"]
    transaction_type: Literal["income", "outcome"]
    establishment: str | None = None
    description: str | None = None
    tax_id: str | None = None


class CreateExpense:
    def __init__(self, repo: ExpenseRepository) -> None:
        self._repo = repo

    async def execute(self, cmd: CreateExpenseCommand) -> Expense:
        extracted = ExtractedExpense(
            amount=cmd.amount,
            date=cmd.date,
            establishment=cmd.establishment,
            description=cmd.description,
            tax_id=cmd.tax_id,
            entry_type=cmd.entry_type,
            transaction_type=cmd.transaction_type,
            confidence=1.0,
        )
        return await self._repo.save(extracted, cmd.category_id)
