from datetime import date
from decimal import Decimal
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, field_validator

from src.models.expense import Expense
from src.routers.deps import get_current_user
from src.services import database

router = APIRouter(prefix="/api/transactions", tags=["transactions"])


class TransactionCreate(BaseModel):
    valor: Decimal
    data: date
    estabelecimento: str | None = None
    descricao: str | None = None
    categoria_id: int | None = None
    cnpj: str | None = None
    tipo_entrada: str = "texto"
    transaction_type: Literal["income", "outcome"] = "outcome"

    @field_validator("valor")
    @classmethod
    def valor_must_be_positive(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("valor deve ser positivo")
        if v > Decimal("999999.99"):
            raise ValueError("valor excede o limite razoável de R$ 999.999,99")
        return v

    @field_validator("transaction_type")
    @classmethod
    def validate_transaction_type(cls, v: str) -> str:
        if v not in ("income", "outcome"):
            raise ValueError("transaction_type deve ser 'income' ou 'outcome'")
        return v


class TransactionUpdate(BaseModel):
    valor: Decimal | None = None
    data: date | None = None
    estabelecimento: str | None = None
    descricao: str | None = None
    categoria_id: int | None = None
    cnpj: str | None = None
    tipo_entrada: str | None = None
    transaction_type: Literal["income", "outcome"] | None = None

    @field_validator("valor")
    @classmethod
    def valor_must_be_positive(cls, v: Decimal | None) -> Decimal | None:
        if v is not None:
            if v <= 0:
                raise ValueError("valor deve ser positivo")
            if v > Decimal("999999.99"):
                raise ValueError("valor excede o limite razoável de R$ 999.999,99")
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
    categoria_id: int | None = None,
    transaction_type: Literal["income", "outcome"] | None = None,
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
    items, total = await database.get_expenses_paginated(
        start, end, categoria_id, page, page_size, transaction_type
    )
    return TransactionPage(items=items, total=total, page=page, page_size=page_size)


@router.get("/{transaction_id}", response_model=Expense)
async def get_transaction(transaction_id: UUID, _user=Depends(get_current_user)):
    expense = await database.get_expense_by_id(str(transaction_id))
    if not expense:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transação não encontrada")
    return expense


@router.post("", response_model=Expense, status_code=status.HTTP_201_CREATED)
async def create_transaction(body: TransactionCreate, _user=Depends(get_current_user)):
    record = {
        "valor": str(body.valor),
        "data": body.data.isoformat(),
        "estabelecimento": body.estabelecimento,
        "descricao": body.descricao,
        "categoria_id": body.categoria_id,
        "cnpj": body.cnpj,
        "tipo_entrada": body.tipo_entrada,
        "transaction_type": body.transaction_type,
        "confianca": 1.0,
        "dados_raw": {},
    }
    return await database.create_expense_direct(record)


@router.put("/{transaction_id}", response_model=Expense)
async def update_transaction(
    transaction_id: UUID, body: TransactionUpdate, _user=Depends(get_current_user)
):
    data = body.model_dump(exclude_none=True)
    if "valor" in data:
        data["valor"] = str(data["valor"])
    if "data" in data:
        data["data"] = data["data"].isoformat()
    expense = await database.update_expense(str(transaction_id), data)
    if not expense:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transação não encontrada")
    return expense


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction(transaction_id: UUID, _user=Depends(get_current_user)):
    deleted = await database.delete_expense(str(transaction_id))
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transação não encontrada")
