from datetime import date
from decimal import Decimal
from typing import Literal, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, field_validator

from src.models.expense import Expense
from src.routers.deps import get_current_user
from src.services import database

router = APIRouter(prefix="/api/transactions", tags=["transactions"])


class TransactionCreate(BaseModel):
    amount: Decimal
    date: date
    establishment: str | None = None
    description: str | None = None
    category_id: int | None = None
    tax_id: str | None = None
    entry_type: str = "texto"
    transaction_type: Literal["income", "outcome"] = "outcome"

    @field_validator("amount")
    @classmethod
    def amount_must_be_positive(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("amount must be positive")
        if v > Decimal("999999.99"):
            raise ValueError("amount exceeds maximum of 999,999.99")
        return v

    @field_validator("transaction_type")
    @classmethod
    def validate_transaction_type(cls, v: str) -> str:
        if v not in ("income", "outcome"):
            raise ValueError("transaction_type must be 'income' or 'outcome'")
        return v


class TransactionUpdate(BaseModel):
    amount: Decimal | None = None
    date: Optional[date] = None
    establishment: str | None = None
    description: str | None = None
    category_id: int | None = None
    tax_id: str | None = None
    entry_type: str | None = None
    transaction_type: Literal["income", "outcome"] | None = None

    @field_validator("amount")
    @classmethod
    def amount_must_be_positive(cls, v: Decimal | None) -> Decimal | None:
        if v is not None:
            if v <= 0:
                raise ValueError("amount must be positive")
            if v > Decimal("999999.99"):
                raise ValueError("amount exceeds maximum of 999,999.99")
        return v


class TransactionPage(BaseModel):
    items: list[Expense]
    total: int
    page: int
    page_size: int


@router.get("", response_model=TransactionPage)
async def list_transactions(
    start: date | None = None,
    end: date | None = None,
    category_id: int | None = None,
    transaction_type: Literal["income", "outcome"] | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1),
    _user=Depends(get_current_user),
):
    if start and end and start > end:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="start must be less than or equal to end",
        )
    page_size = min(page_size, 100)
    items, total = await database.get_expenses_paginated(
        start, end, category_id, page, page_size, transaction_type
    )
    return TransactionPage(items=items, total=total, page=page, page_size=page_size)


@router.get("/{transaction_id}", response_model=Expense)
async def get_transaction(transaction_id: UUID, _user=Depends(get_current_user)):
    expense = await database.get_expense_by_id(str(transaction_id))
    if not expense:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    return expense


@router.post("", response_model=Expense, status_code=status.HTTP_201_CREATED)
async def create_transaction(body: TransactionCreate, _user=Depends(get_current_user)):
    record = {
        "amount": str(body.amount),
        "date": body.date.isoformat(),
        "establishment": body.establishment,
        "description": body.description,
        "category_id": body.category_id,
        "tax_id": body.tax_id,
        "entry_type": body.entry_type,
        "transaction_type": body.transaction_type,
        "confidence": 1.0,
        "raw_data": {},
    }
    return await database.create_expense_direct(record)


@router.put("/{transaction_id}", response_model=Expense)
async def update_transaction(
    transaction_id: UUID, body: TransactionUpdate, _user=Depends(get_current_user)
):
    data = body.model_dump(exclude_none=True)
    if "amount" in data:
        data["amount"] = str(data["amount"])
    if "date" in data:
        data["date"] = data["date"].isoformat()
    expense = await database.update_expense(str(transaction_id), data)
    if not expense:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    return expense


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction(transaction_id: UUID, _user=Depends(get_current_user)):
    deleted = await database.delete_expense(str(transaction_id))
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
