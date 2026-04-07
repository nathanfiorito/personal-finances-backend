from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from src.routers.deps import get_current_user
from src.services import database

router = APIRouter(prefix="/api/reports", tags=["reports"])


class SummaryItem(BaseModel):
    categoria: str
    total: Decimal


class MonthlyCategoryItem(BaseModel):
    categoria: str
    total: Decimal


class MonthlyItem(BaseModel):
    month: int
    total: Decimal
    by_category: list[MonthlyCategoryItem]


@router.get("/summary", response_model=list[SummaryItem])
async def get_summary(
    start: date,
    end: date,
    transaction_type: Literal["income", "outcome"] | None = None,
    _user=Depends(get_current_user),
):
    if start > end:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="start deve ser menor ou igual a end",
        )
    totals = await database.get_totals_by_category(start, end, transaction_type)
    return sorted(
        [SummaryItem(categoria=k, total=v) for k, v in totals.items()],
        key=lambda x: x.total,
        reverse=True,
    )


@router.get("/monthly", response_model=list[MonthlyItem])
async def get_monthly(
    year: int = Query(default=None),
    transaction_type: Literal["income", "outcome"] | None = None,
    _user=Depends(get_current_user),
):
    if year is None:
        year = datetime.now().year

    expenses = await database.get_expenses_by_year(year, transaction_type)

    monthly: dict[int, dict[str, Decimal]] = defaultdict(lambda: defaultdict(Decimal))
    for exp in expenses:
        monthly[exp.data.month][exp.categoria] += exp.valor

    result = []
    for month in sorted(monthly.keys()):
        by_category = sorted(
            [MonthlyCategoryItem(categoria=k, total=v) for k, v in monthly[month].items()],
            key=lambda x: x.total,
            reverse=True,
        )
        total = sum((item.total for item in by_category), Decimal("0"))
        result.append(MonthlyItem(month=month, total=total, by_category=by_category))

    return result
