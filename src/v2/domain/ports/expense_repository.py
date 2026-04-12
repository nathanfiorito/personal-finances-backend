from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Literal
from uuid import UUID

from src.v2.domain.entities.expense import Expense, ExtractedExpense


@dataclass
class ExpenseFilters:
    start: date | None = None
    end: date | None = None
    category_id: int | None = None
    transaction_type: Literal["income", "outcome"] | None = None
    page: int = 1
    page_size: int = 20


@dataclass
class ExpenseUpdate:
    amount: Decimal | None = None
    date: date | None = None
    establishment: str | None = None
    description: str | None = None
    category_id: int | None = None
    tax_id: str | None = None
    entry_type: str | None = None
    transaction_type: Literal["income", "outcome"] | None = None


class ExpenseRepository(ABC):
    @abstractmethod
    async def save(self, expense: ExtractedExpense, category_id: int) -> Expense: ...

    @abstractmethod
    async def get_by_id(self, expense_id: UUID) -> Expense | None: ...

    @abstractmethod
    async def list_paginated(
        self, filters: ExpenseFilters
    ) -> tuple[list[Expense], int]: ...

    @abstractmethod
    async def list_by_period(
        self,
        start: date,
        end: date,
        transaction_type: str | None = None,
    ) -> list[Expense]: ...

    @abstractmethod
    async def get_recent(self, limit: int = 3) -> list[Expense]: ...

    @abstractmethod
    async def update(
        self, expense_id: UUID, data: ExpenseUpdate
    ) -> Expense | None: ...

    @abstractmethod
    async def delete(self, expense_id: UUID) -> bool: ...
