from datetime import date
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, field_validator

from src.models.expense import Expense
from src.routers.deps import get_current_user
from src.services import database

router = APIRouter(prefix="/api/expenses", tags=["expenses"])


class ExpenseCreate(BaseModel):
    valor: Decimal
    data: date
    estabelecimento: str | None = None
    descricao: str | None = None
    categoria_id: int
    cnpj: str | None = None
    tipo_entrada: str = "texto"

    @field_validator("valor")
    @classmethod
    def valor_must_be_positive(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("valor deve ser positivo")
        if v > Decimal("999999.99"):
            raise ValueError("valor excede o limite razoável de R$ 999.999,99")
        return v


class ExpenseUpdate(BaseModel):
    valor: Decimal | None = None
    data: date | None = None
    estabelecimento: str | None = None
    descricao: str | None = None
    categoria_id: int | None = None
    cnpj: str | None = None

    @field_validator("valor")
    @classmethod
    def valor_must_be_positive(cls, v: Decimal | None) -> Decimal | None:
        if v is not None:
            if v <= 0:
                raise ValueError("valor deve ser positivo")
            if v > Decimal("999999.99"):
                raise ValueError("valor excede o limite razoável de R$ 999.999,99")
        return v


class ExpensePage(BaseModel):
    items: list[Expense]
    total: int
    page: int
    page_size: int


@router.get("", response_model=ExpensePage)
async def list_expenses(
    start: date | None = None,
    end: date | None = None,
    categoria_id: int | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1),
    _user=Depends(get_current_user),
):
    if start and end and start > end:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="start deve ser menor ou igual a end",
        )
    page_size = min(page_size, 100)
    items, total = await database.get_expenses_paginated(start, end, categoria_id, page, page_size)
    return ExpensePage(items=items, total=total, page=page, page_size=page_size)


@router.get("/{expense_id}", response_model=Expense)
async def get_expense(expense_id: UUID, _user=Depends(get_current_user)):
    expense = await database.get_expense_by_id(str(expense_id))
    if not expense:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Despesa não encontrada")
    return expense


@router.post("", response_model=Expense, status_code=status.HTTP_201_CREATED)
async def create_expense(body: ExpenseCreate, _user=Depends(get_current_user)):
    record = {
        "valor": str(body.valor),
        "data": body.data.isoformat(),
        "estabelecimento": body.estabelecimento,
        "descricao": body.descricao,
        "categoria_id": body.categoria_id,
        "cnpj": body.cnpj,
        "tipo_entrada": body.tipo_entrada,
        "confianca": 1.0,
        "dados_raw": {},
    }
    return await database.create_expense_direct(record)


@router.put("/{expense_id}", response_model=Expense)
async def update_expense(expense_id: UUID, body: ExpenseUpdate, _user=Depends(get_current_user)):
    data = body.model_dump(exclude_none=True)
    if "valor" in data:
        data["valor"] = str(data["valor"])
    if "data" in data:
        data["data"] = data["data"].isoformat()
    expense = await database.update_expense(str(expense_id), data)
    if not expense:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Despesa não encontrada")
    return expense


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_expense(expense_id: UUID, _user=Depends(get_current_user)):
    deleted = await database.delete_expense(str(expense_id))
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Despesa não encontrada")
