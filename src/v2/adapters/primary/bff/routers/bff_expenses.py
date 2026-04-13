from __future__ import annotations

import asyncio
from datetime import date as _date
from typing import Literal

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from src.v2.adapters.primary.bff.deps import (
    get_current_user,
    get_list_categories,
    get_list_expenses,
)
from src.v2.domain.entities.category import Category
from src.v2.domain.entities.expense import Expense
from src.v2.domain.use_cases.expenses.list_expenses import ListExpensesQuery

router = APIRouter(prefix="/api/v2/bff", tags=["v2-bff"])


class TransactionPage(BaseModel):
    items: list[Expense]
    total: int
    page: int
    page_size: int


class ExpensesPageResponse(BaseModel):
    transactions: TransactionPage
    categories: list[Category]


@router.get("/expenses", response_model=ExpensesPageResponse)
async def get_expenses_page(
    start: _date | None = None,
    end: _date | None = None,
    category_id: int | None = None,
    transaction_type: Literal["income", "expense"] | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    _user=Depends(get_current_user),
    list_uc=Depends(get_list_expenses),
    categories_uc=Depends(get_list_categories),
):
    (items, total), categories = await asyncio.gather(
        list_uc.execute(
            ListExpensesQuery(
                start=start,
                end=end,
                category_id=category_id,
                transaction_type=transaction_type,
                page=page,
                page_size=page_size,
            )
        ),
        categories_uc.execute(),
    )
    return ExpensesPageResponse(
        transactions=TransactionPage(items=items, total=total, page=page, page_size=page_size),
        categories=categories,
    )
