from datetime import date as _date
from typing import Literal, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from src.v2.adapters.primary.bff.deps import (
    get_current_user,
    get_get_monthly,
    get_get_summary,
)
from src.v2.domain.use_cases.reports.get_monthly import GetMonthlyQuery
from src.v2.domain.use_cases.reports.get_summary import GetSummaryQuery

router = APIRouter(prefix="/api/v2/reports", tags=["v2-reports"])


class SummaryItemOut(BaseModel):
    category: str
    total: str


class MonthlyByCategoryOut(BaseModel):
    category: str
    total: str


class MonthlyItemOut(BaseModel):
    month: int
    total: str
    by_category: list[MonthlyByCategoryOut]


@router.get("/summary", response_model=list[SummaryItemOut])
async def get_summary(
    start: _date,
    end: _date,
    transaction_type: Optional[Literal["income", "outcome"]] = None,
    _user=Depends(get_current_user),
    use_case=Depends(get_get_summary),
):
    items = await use_case.execute(
        GetSummaryQuery(start=start, end=end, transaction_type=transaction_type)
    )
    return [SummaryItemOut(category=i.category, total=str(i.total)) for i in items]


@router.get("/monthly", response_model=list[MonthlyItemOut])
async def get_monthly(
    year: int,
    transaction_type: Optional[Literal["income", "outcome"]] = None,
    _user=Depends(get_current_user),
    use_case=Depends(get_get_monthly),
):
    items = await use_case.execute(
        GetMonthlyQuery(year=year, transaction_type=transaction_type)
    )
    return [
        MonthlyItemOut(
            month=i.month,
            total=str(i.total),
            by_category=[
                MonthlyByCategoryOut(category=b.category, total=str(b.total))
                for b in i.by_category
            ],
        )
        for i in items
    ]
