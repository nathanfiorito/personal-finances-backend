from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from src.v2.adapters.primary.bff.deps import (
    get_current_user,
    get_get_monthly,
)
from src.v2.domain.use_cases.reports.get_monthly import GetMonthlyQuery

router = APIRouter(prefix="/api/v2/reports", tags=["v2-reports"])


class MonthlyByCategoryOut(BaseModel):
    category: str
    total: str


class MonthlyItemOut(BaseModel):
    month: int
    total: str
    by_category: list[MonthlyByCategoryOut]


@router.get("/monthly", response_model=list[MonthlyItemOut])
async def get_monthly(
    year: int,
    transaction_type: Literal["income", "outcome"] | None = None,
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
