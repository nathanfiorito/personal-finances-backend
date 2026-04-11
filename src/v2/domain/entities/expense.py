from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator


class ExtractedExpense(BaseModel):
    """Expense data extracted from a receipt by the LLM. Not yet persisted."""

    amount: Decimal
    date: Any = None
    establishment: Any = None
    description: Any = None
    tax_id: Any = None
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
    def format_tax_id(cls, v: Any) -> Any:
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
    establishment: Any
    description: Any
    category_id: int
    category: str
    tax_id: Any
    entry_type: str
    transaction_type: Literal["income", "outcome"]
    confidence: Any
    created_at: datetime
