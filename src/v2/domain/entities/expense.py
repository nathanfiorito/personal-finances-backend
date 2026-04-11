from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class ExtractedExpense(BaseModel):
    """Expense data extracted from a receipt by the LLM. Not yet persisted."""

    amount: Decimal
    date: date | None = None
    establishment: str | None = None
    description: str | None = None
    tax_id: str | None = None
    entry_type: Literal["image", "text", "pdf"]
    transaction_type: Literal["income", "outcome"] = "outcome"
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)

    @field_validator("amount")
    @classmethod
    def amount_must_be_positive(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("Amount must be positive")
        if v > Decimal("999999.99"):
            raise ValueError("Amount exceeds reasonable limit of 999,999.99")
        return v

    @field_validator("tax_id")
    @classmethod
    def format_tax_id(cls, v: str | None) -> str | None:
        if v is None:
            return None
        digits = "".join(c for c in v if c.isdigit())
        if len(digits) == 14:
            return f"{digits[:2]}.{digits[2:5]}.{digits[5:8]}/{digits[8:12]}-{digits[12:]}"
        return v


class Expense(BaseModel):
    """A persisted expense record from the database."""

    id: UUID
    amount: Decimal
    date: date
    establishment: str | None
    description: str | None
    category_id: int
    category: str
    tax_id: str | None
    entry_type: str
    transaction_type: Literal["income", "outcome"]
    confidence: float | None
    created_at: datetime
