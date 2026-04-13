from __future__ import annotations

import asyncio
from datetime import date as _date

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from src.v2.adapters.primary.bff.deps import (
    get_current_user,
    get_get_summary,
    get_list_expenses,
)
from src.v2.domain.use_cases.expenses.list_expenses import ListExpensesQuery
from src.v2.domain.use_cases.reports.get_summary import GetSummaryQuery

router = APIRouter(prefix="/api/v2/bff", tags=["v2-bff"])


class SummaryItemOut(BaseModel):
    category: str
    total: str


class DashboardResponse(BaseModel):
    expense_summary: list[SummaryItemOut]
    income_summary: list[SummaryItemOut]
    transaction_count: int


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(
    start: _date,
    end: _date,
    _user=Depends(get_current_user),
    summary_uc=Depends(get_get_summary),
    list_uc=Depends(get_list_expenses),
):
    if start > end:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="start must be <= end",
        )
    expense_items, income_items, list_result = await asyncio.gather(
        summary_uc.execute(GetSummaryQuery(start=start, end=end, transaction_type="expense")),
        summary_uc.execute(GetSummaryQuery(start=start, end=end, transaction_type="income")),
        list_uc.execute(ListExpensesQuery(start=start, end=end, page=1, page_size=1)),
    )
    _, total = list_result
    return DashboardResponse(
        expense_summary=[
            SummaryItemOut(category=i.category, total=str(i.total)) for i in expense_items
        ],
        income_summary=[
            SummaryItemOut(category=i.category, total=str(i.total)) for i in income_items
        ],
        transaction_count=total,
    )
