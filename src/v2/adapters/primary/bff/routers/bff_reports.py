from __future__ import annotations

import asyncio
from decimal import Decimal

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from src.v2.adapters.primary.bff.deps import (
    get_current_user,
    get_get_monthly,
)
from src.v2.domain.use_cases.reports.get_monthly import GetMonthlyQuery

router = APIRouter(prefix="/api/v2/bff", tags=["v2-bff"])


class ReportByCategoryOut(BaseModel):
    category: str
    total: str


class ReportMonthOut(BaseModel):
    month: int
    income_total: str
    expense_total: str
    expense_by_category: list[ReportByCategoryOut]


@router.get("/reports", response_model=list[ReportMonthOut])
async def get_reports(
    year: int,
    _user=Depends(get_current_user),
    use_case=Depends(get_get_monthly),
):
    expense_items, income_items = await asyncio.gather(
        use_case.execute(GetMonthlyQuery(year=year, transaction_type="expense")),
        use_case.execute(GetMonthlyQuery(year=year, transaction_type="income")),
    )

    expense_by_month = {i.month: i for i in expense_items}
    income_by_month = {i.month: i for i in income_items}
    all_months = sorted(set(expense_by_month) | set(income_by_month))

    return [
        ReportMonthOut(
            month=month,
            income_total=str(
                income_by_month[month].total if month in income_by_month else Decimal("0.00")
            ),
            expense_total=str(
                expense_by_month[month].total if month in expense_by_month else Decimal("0.00")
            ),
            expense_by_category=[
                ReportByCategoryOut(category=b.category, total=str(b.total))
                for b in (expense_by_month[month].by_category if month in expense_by_month else [])
            ],
        )
        for month in all_months
    ]
