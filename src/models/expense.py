from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class ExtractedExpense(BaseModel):
    valor: Decimal
    data: date
    estabelecimento: str | None = None
    descricao: str | None = None
    cnpj: str | None = None
    tipo_entrada: Literal["imagem", "texto", "pdf"]
    confianca: float = Field(ge=0.0, le=1.0, default=0.5)
    dados_raw: dict = Field(default_factory=dict)

    @field_validator("valor")
    @classmethod
    def valor_must_be_positive(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("valor deve ser positivo")
        return v

    @field_validator("cnpj")
    @classmethod
    def format_cnpj(cls, v: str | None) -> str | None:
        if v is None:
            return None
        digits = "".join(c for c in v if c.isdigit())
        if len(digits) == 14:
            return f"{digits[:2]}.{digits[2:5]}.{digits[5:8]}/{digits[8:12]}-{digits[12:]}"
        return v


class Expense(BaseModel):
    id: UUID
    valor: Decimal
    data: date
    estabelecimento: str | None
    descricao: str | None
    categoria: str
    cnpj: str | None
    tipo_entrada: str
    confianca: float | None
    created_at: datetime
