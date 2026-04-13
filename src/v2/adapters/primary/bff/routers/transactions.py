from __future__ import annotations

from datetime import date as _date
from decimal import Decimal
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, field_validator

from src.v2.adapters.primary.bff.deps import (
    domain_exception_handler,
    get_create_expense,
    get_current_user,
    get_delete_expense,
    get_update_expense,
)
from src.v2.domain.entities.expense import Expense
from src.v2.domain.exceptions import DomainError
from src.v2.domain.use_cases.expenses.create_expense import CreateExpenseCommand
from src.v2.domain.use_cases.expenses.delete_expense import DeleteExpenseCommand
from src.v2.domain.use_cases.expenses.update_expense import UpdateExpenseCommand

router = APIRouter(prefix="/api/v2/transactions", tags=["v2-transactions"])


class TransactionCreate(BaseModel):
    amount: Decimal
    date: _date | None = None
    category_id: int
    entry_type: str = "text"
    transaction_type: Literal["income", "outcome"] = "outcome"
    payment_method: Literal["credit", "debit"]
    establishment: str | None = None
    description: str | None = None
    tax_id: str | None = None

    @field_validator("amount")
    @classmethod
    def amount_positive(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("amount must be positive")
        if v > Decimal("999999.99"):
            raise ValueError("amount exceeds limit")
        return v


class TransactionUpdate(BaseModel):
    amount: Decimal | None = None
    date: _date | None = None
    category_id: int | None = None
    entry_type: str | None = None
    transaction_type: Literal["income", "outcome"] | None = None
    payment_method: Literal["credit", "debit"] | None = None
    establishment: str | None = None
    description: str | None = None
    tax_id: str | None = None


@router.post("", response_model=Expense, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    body: TransactionCreate,
    _user=Depends(get_current_user),
    use_case=Depends(get_create_expense),
):
    return await use_case.execute(
        CreateExpenseCommand(
            amount=body.amount,
            date=body.date,
            category_id=body.category_id,
            entry_type=body.entry_type,
            transaction_type=body.transaction_type,
            payment_method=body.payment_method,
            establishment=body.establishment,
            description=body.description,
            tax_id=body.tax_id,
        )
    )


@router.put("/{transaction_id}", response_model=Expense)
async def update_transaction(
    transaction_id: UUID,
    body: TransactionUpdate,
    _user=Depends(get_current_user),
    use_case=Depends(get_update_expense),
):
    try:
        return await use_case.execute(
            UpdateExpenseCommand(
                expense_id=transaction_id,
                amount=body.amount,
                date=body.date,
                category_id=body.category_id,
                entry_type=body.entry_type,
                transaction_type=body.transaction_type,
                payment_method=body.payment_method,
                establishment=body.establishment,
                description=body.description,
                tax_id=body.tax_id,
            )
        )
    except DomainError as exc:
        raise domain_exception_handler(exc)


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction(
    transaction_id: UUID,
    _user=Depends(get_current_user),
    use_case=Depends(get_delete_expense),
):
    try:
        await use_case.execute(DeleteExpenseCommand(expense_id=transaction_id))
    except DomainError as exc:
        raise domain_exception_handler(exc)
