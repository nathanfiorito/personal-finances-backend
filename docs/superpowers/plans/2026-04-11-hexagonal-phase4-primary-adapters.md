# Hexagonal Architecture — Phase 4: Primary Adapters + Integration

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the BFF (FastAPI routers) and Telegram primary adapters, wire everything through `bootstrap.py`, and mount v2 alongside v1 in `main.py`. Frontend routes move to `/api/v2/...` while v1 stays live.

**Architecture:** Primary adapters call use cases. Use cases live on `app.state.use_cases` (populated by `bootstrap.py`). FastAPI `Depends()` reads from `request.app.state` — no DI framework needed. BFF tests use `TestClient` with stub use cases. The Telegram webhook URL does not change.

**Tech Stack:** Python 3.12, FastAPI, httpx, pytest, supabase-py

**Prerequisite:** Phases 1–3 complete. `pytest tests/v2/` passes.

**Spec:** `docs/superpowers/specs/2026-04-11-hexagonal-architecture-design.md`

---

## File Map

**Create:**
- `src/v2/adapters/primary/bff/deps.py`
- `src/v2/adapters/primary/bff/routers/transactions.py`
- `src/v2/adapters/primary/bff/routers/categories.py`
- `src/v2/adapters/primary/bff/routers/reports.py`
- `src/v2/adapters/primary/bff/routers/export.py`
- `src/v2/adapters/primary/telegram/webhook.py`
- `src/v2/adapters/primary/telegram/handlers/message.py`
- `src/v2/adapters/primary/telegram/handlers/commands.py`
- `src/v2/adapters/primary/telegram/handlers/callback.py`
- `src/v2/bootstrap.py`
- `tests/v2/adapters/test_bff_transactions.py`
- `tests/v2/adapters/test_bff_categories.py`

**Modify:**
- `src/main.py` — include v2 routers alongside v1

---

## Task 15: BFF deps and auth

**Files:**
- Create: `src/v2/adapters/primary/bff/deps.py`

The BFF reuses v1's JWT auth pattern (`get_current_user`). Use cases are retrieved from `request.app.state.use_cases`.

- [ ] **Step 1: Create `src/v2/adapters/primary/bff/deps.py`**

```python
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.config.settings import settings
from src.v2.domain.exceptions import (
    CategoryNotFoundError,
    DomainError,
    ExpenseNotFoundError,
)

_bearer = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> dict:
    """Validate Supabase JWT. Returns the decoded payload.

    Delegates to the same logic as v1's deps.py to avoid duplication.
    """
    from src.routers.deps import get_current_user as _v1_get_current_user
    # Re-use v1 auth — identical JWT validation logic.
    return await _v1_get_current_user(credentials)


def domain_exception_handler(exc: DomainError) -> HTTPException:
    """Map domain exceptions to HTTP status codes."""
    if isinstance(exc, (ExpenseNotFoundError, CategoryNotFoundError)):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        )
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
    )


# ── Use-case accessors (read from app.state) ──────────────────────────────────
# Each accessor is a FastAPI dependency that reads the pre-built use case
# instance wired by bootstrap.py.

def _uc(request: Request):
    return request.app.state.use_cases


def get_create_expense(request: Request):
    return _uc(request).create_expense


def get_list_expenses(request: Request):
    return _uc(request).list_expenses


def get_get_expense(request: Request):
    return _uc(request).get_expense


def get_update_expense(request: Request):
    return _uc(request).update_expense


def get_delete_expense(request: Request):
    return _uc(request).delete_expense


def get_list_categories(request: Request):
    return _uc(request).list_categories


def get_create_category(request: Request):
    return _uc(request).create_category


def get_update_category(request: Request):
    return _uc(request).update_category


def get_deactivate_category(request: Request):
    return _uc(request).deactivate_category


def get_get_summary(request: Request):
    return _uc(request).get_summary


def get_get_monthly(request: Request):
    return _uc(request).get_monthly


def get_export_csv(request: Request):
    return _uc(request).export_csv
```

- [ ] **Step 2: Commit**

```bash
git add src/v2/adapters/primary/bff/deps.py
git commit -m "feat(v2): add BFF deps (auth + use-case accessors)"
```

---

## Task 16: BFF transactions router

**Files:**
- Create: `src/v2/adapters/primary/bff/routers/transactions.py`
- Create: `tests/v2/adapters/test_bff_transactions.py`

- [ ] **Step 1: Write `tests/v2/adapters/test_bff_transactions.py`**

```python
import datetime as _dt
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.v2.adapters.primary.bff.routers.transactions import router
from src.v2.domain.entities.expense import Expense
from src.v2.domain.exceptions import ExpenseNotFoundError


def _make_expense() -> Expense:
    return Expense(
        id=uuid4(),
        amount=Decimal("50.00"),
        date=_dt.date(2026, 1, 15),
        establishment="Store",
        description=None,
        category_id=1,
        category="Alimentação",
        tax_id=None,
        entry_type="text",
        transaction_type="outcome",
        confidence=0.9,
        created_at=_dt.datetime(2026, 1, 15, 10, 0),
    )


def _app(use_cases: SimpleNamespace) -> FastAPI:
    app = FastAPI()
    app.state.use_cases = use_cases

    # Bypass auth for tests
    from src.v2.adapters.primary.bff import deps
    app.dependency_overrides[deps.get_current_user] = lambda: {"sub": "test-user"}
    app.include_router(router)
    return app


class StubListExpenses:
    async def execute(self, query):
        return [_make_expense()], 1


class StubGetExpense:
    def __init__(self, found: bool = True):
        self._found = found

    async def execute(self, query):
        if not self._found:
            raise ExpenseNotFoundError("not found")
        return _make_expense()


class StubCreateExpense:
    async def execute(self, cmd):
        return _make_expense()


class StubUpdateExpense:
    def __init__(self, found: bool = True):
        self._found = found

    async def execute(self, cmd):
        if not self._found:
            raise ExpenseNotFoundError("not found")
        return _make_expense()


class StubDeleteExpense:
    def __init__(self, found: bool = True):
        self._found = found

    async def execute(self, cmd):
        if not self._found:
            raise ExpenseNotFoundError("not found")


def test_list_transactions_returns_200():
    uc = SimpleNamespace(
        list_expenses=StubListExpenses(),
        get_expense=StubGetExpense(),
        create_expense=StubCreateExpense(),
        update_expense=StubUpdateExpense(),
        delete_expense=StubDeleteExpense(),
    )
    client = TestClient(_app(uc))
    resp = client.get("/api/v2/transactions")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert len(body["items"]) == 1


def test_get_transaction_returns_200_when_found():
    expense = _make_expense()

    class FoundStub:
        async def execute(self, q):
            return expense

    uc = SimpleNamespace(
        list_expenses=StubListExpenses(),
        get_expense=FoundStub(),
        create_expense=StubCreateExpense(),
        update_expense=StubUpdateExpense(),
        delete_expense=StubDeleteExpense(),
    )
    client = TestClient(_app(uc))
    resp = client.get(f"/api/v2/transactions/{expense.id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == str(expense.id)


def test_get_transaction_returns_404_when_not_found():
    uc = SimpleNamespace(
        list_expenses=StubListExpenses(),
        get_expense=StubGetExpense(found=False),
        create_expense=StubCreateExpense(),
        update_expense=StubUpdateExpense(),
        delete_expense=StubDeleteExpense(),
    )
    client = TestClient(_app(uc))
    resp = client.get(f"/api/v2/transactions/{uuid4()}")
    assert resp.status_code == 404


def test_create_transaction_returns_201():
    uc = SimpleNamespace(
        list_expenses=StubListExpenses(),
        get_expense=StubGetExpense(),
        create_expense=StubCreateExpense(),
        update_expense=StubUpdateExpense(),
        delete_expense=StubDeleteExpense(),
    )
    client = TestClient(_app(uc))
    resp = client.post(
        "/api/v2/transactions",
        json={
            "amount": "50.00",
            "date": "2026-01-15",
            "category_id": 1,
            "entry_type": "text",
            "transaction_type": "outcome",
        },
    )
    assert resp.status_code == 201


def test_delete_transaction_returns_204():
    expense = _make_expense()

    class DeleteStub:
        async def execute(self, cmd):
            pass

    uc = SimpleNamespace(
        list_expenses=StubListExpenses(),
        get_expense=StubGetExpense(),
        create_expense=StubCreateExpense(),
        update_expense=StubUpdateExpense(),
        delete_expense=DeleteStub(),
    )
    client = TestClient(_app(uc))
    resp = client.delete(f"/api/v2/transactions/{expense.id}")
    assert resp.status_code == 204
```

- [ ] **Step 2: Run tests — expect FAIL**

```bash
pytest tests/v2/adapters/test_bff_transactions.py -v
```

Expected: `ImportError`

- [ ] **Step 3: Create `src/v2/adapters/primary/bff/routers/transactions.py`**

```python
from datetime import date
from decimal import Decimal
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, field_validator

from src.v2.adapters.primary.bff.deps import (
    domain_exception_handler,
    get_create_expense,
    get_delete_expense,
    get_get_expense,
    get_list_expenses,
    get_update_expense,
    get_current_user,
)
from src.v2.domain.entities.expense import Expense
from src.v2.domain.exceptions import DomainError
from src.v2.domain.use_cases.expenses.create_expense import CreateExpenseCommand
from src.v2.domain.use_cases.expenses.delete_expense import DeleteExpenseCommand
from src.v2.domain.use_cases.expenses.get_expense import GetExpenseQuery
from src.v2.domain.use_cases.expenses.list_expenses import ListExpensesQuery
from src.v2.domain.use_cases.expenses.update_expense import UpdateExpenseCommand

router = APIRouter(prefix="/api/v2/transactions", tags=["v2-transactions"])


class TransactionCreate(BaseModel):
    amount: Decimal
    date: date
    category_id: int
    entry_type: str = "text"
    transaction_type: Literal["income", "outcome"] = "outcome"
    establishment: str | None = None
    description: str | None = None
    tax_id: str | None = None

    @field_validator("amount")
    @classmethod
    def amount_positive(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("amount must be positive")
        if v > Decimal("999999.99"):
            raise ValueError("amount exceeds limit")
        return v


class TransactionUpdate(BaseModel):
    amount: Decimal | None = None
    date: date | None = None
    category_id: int | None = None
    entry_type: str | None = None
    transaction_type: Literal["income", "outcome"] | None = None
    establishment: str | None = None
    description: str | None = None
    tax_id: str | None = None


class TransactionPage(BaseModel):
    items: list[Expense]
    total: int
    page: int
    page_size: int


@router.get("", response_model=TransactionPage)
async def list_transactions(
    request: Request,
    start: date | None = None,
    end: date | None = None,
    category_id: int | None = None,
    transaction_type: Literal["income", "outcome"] | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1),
    _user=Depends(get_current_user),
    use_case=Depends(get_list_expenses),
):
    if start and end and start > end:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="start must be <= end",
        )
    items, total = await use_case.execute(
        ListExpensesQuery(
            start=start,
            end=end,
            category_id=category_id,
            transaction_type=transaction_type,
            page=page,
            page_size=page_size,
        )
    )
    return TransactionPage(items=items, total=total, page=page, page_size=page_size)


@router.get("/{transaction_id}", response_model=Expense)
async def get_transaction(
    transaction_id: UUID,
    _user=Depends(get_current_user),
    use_case=Depends(get_get_expense),
):
    try:
        return await use_case.execute(GetExpenseQuery(expense_id=transaction_id))
    except DomainError as exc:
        raise domain_exception_handler(exc)


@router.post("", response_model=Expense, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    body: TransactionCreate,
    _user=Depends(get_current_user),
    use_case=Depends(get_create_expense),
):
    return await use_case.execute(
        CreateExpenseCommand(
            amount=body.amount,
            date=body.date,
            category_id=body.category_id,
            entry_type=body.entry_type,
            transaction_type=body.transaction_type,
            establishment=body.establishment,
            description=body.description,
            tax_id=body.tax_id,
        )
    )


@router.put("/{transaction_id}", response_model=Expense)
async def update_transaction(
    transaction_id: UUID,
    body: TransactionUpdate,
    _user=Depends(get_current_user),
    use_case=Depends(get_update_expense),
):
    try:
        return await use_case.execute(
            UpdateExpenseCommand(
                expense_id=transaction_id,
                amount=body.amount,
                date=body.date,
                category_id=body.category_id,
                entry_type=body.entry_type,
                transaction_type=body.transaction_type,
                establishment=body.establishment,
                description=body.description,
                tax_id=body.tax_id,
            )
        )
    except DomainError as exc:
        raise domain_exception_handler(exc)


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction(
    transaction_id: UUID,
    _user=Depends(get_current_user),
    use_case=Depends(get_delete_expense),
):
    try:
        await use_case.execute(DeleteExpenseCommand(expense_id=transaction_id))
    except DomainError as exc:
        raise domain_exception_handler(exc)
```

- [ ] **Step 4: Run tests — expect PASS**

```bash
pytest tests/v2/adapters/test_bff_transactions.py -v
```

Expected: `5 passed`

- [ ] **Step 5: Commit**

```bash
git add src/v2/adapters/primary/bff/routers/transactions.py tests/v2/adapters/test_bff_transactions.py
git commit -m "feat(v2): add BFF transactions router with tests"
```

---

## Task 17: BFF categories, reports, and export routers

**Files:**
- Create: `src/v2/adapters/primary/bff/routers/categories.py`
- Create: `src/v2/adapters/primary/bff/routers/reports.py`
- Create: `src/v2/adapters/primary/bff/routers/export.py`
- Create: `tests/v2/adapters/test_bff_categories.py`

- [ ] **Step 1: Write `tests/v2/adapters/test_bff_categories.py`**

```python
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.v2.adapters.primary.bff.routers.categories import router
from src.v2.domain.entities.category import Category
from src.v2.domain.exceptions import CategoryNotFoundError


def _app(use_cases: SimpleNamespace) -> FastAPI:
    app = FastAPI()
    app.state.use_cases = use_cases
    from src.v2.adapters.primary.bff import deps
    app.dependency_overrides[deps.get_current_user] = lambda: {"sub": "test-user"}
    app.include_router(router)
    return app


class StubListCategories:
    async def execute(self):
        return [
            Category(id=1, name="Alimentação", is_active=True),
            Category(id=2, name="Transporte", is_active=True),
        ]


class StubCreateCategory:
    async def execute(self, cmd):
        return Category(id=3, name=cmd.name, is_active=True)


class StubUpdateCategory:
    def __init__(self, found: bool = True):
        self._found = found

    async def execute(self, cmd):
        if not self._found:
            raise CategoryNotFoundError("not found")
        return Category(id=cmd.category_id, name=cmd.name or "Updated", is_active=True)


class StubDeactivateCategory:
    def __init__(self, found: bool = True):
        self._found = found

    async def execute(self, cmd):
        if not self._found:
            raise CategoryNotFoundError("not found")


def _default_uc():
    return SimpleNamespace(
        list_categories=StubListCategories(),
        create_category=StubCreateCategory(),
        update_category=StubUpdateCategory(),
        deactivate_category=StubDeactivateCategory(),
    )


def test_list_categories_returns_200():
    client = TestClient(_app(_default_uc()))
    resp = client.get("/api/v2/categories")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_create_category_returns_201():
    client = TestClient(_app(_default_uc()))
    resp = client.post("/api/v2/categories", json={"name": "Pets"})
    assert resp.status_code == 201
    assert resp.json()["name"] == "Pets"


def test_update_category_returns_200():
    client = TestClient(_app(_default_uc()))
    resp = client.patch("/api/v2/categories/1", json={"name": "Comida"})
    assert resp.status_code == 200


def test_update_category_returns_404_when_not_found():
    uc = SimpleNamespace(
        list_categories=StubListCategories(),
        create_category=StubCreateCategory(),
        update_category=StubUpdateCategory(found=False),
        deactivate_category=StubDeactivateCategory(),
    )
    client = TestClient(_app(uc))
    resp = client.patch("/api/v2/categories/999", json={"name": "X"})
    assert resp.status_code == 404


def test_delete_category_returns_204():
    client = TestClient(_app(_default_uc()))
    resp = client.delete("/api/v2/categories/1")
    assert resp.status_code == 204
```

- [ ] **Step 2: Run tests — expect FAIL**

```bash
pytest tests/v2/adapters/test_bff_categories.py -v
```

Expected: `ImportError`

- [ ] **Step 3: Create `src/v2/adapters/primary/bff/routers/categories.py`**

```python
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel

from src.v2.adapters.primary.bff.deps import (
    domain_exception_handler,
    get_create_category,
    get_deactivate_category,
    get_list_categories,
    get_update_category,
    get_current_user,
)
from src.v2.domain.entities.category import Category
from src.v2.domain.exceptions import DomainError
from src.v2.domain.use_cases.categories.create_category import CreateCategoryCommand
from src.v2.domain.use_cases.categories.deactivate_category import DeactivateCategoryCommand
from src.v2.domain.use_cases.categories.update_category import UpdateCategoryCommand

router = APIRouter(prefix="/api/v2/categories", tags=["v2-categories"])


class CategoryCreate(BaseModel):
    name: str


class CategoryPatch(BaseModel):
    name: str | None = None
    is_active: bool | None = None


@router.get("", response_model=list[Category])
async def list_categories(
    _user=Depends(get_current_user),
    use_case=Depends(get_list_categories),
):
    return await use_case.execute()


@router.post("", response_model=Category, status_code=status.HTTP_201_CREATED)
async def create_category(
    body: CategoryCreate,
    _user=Depends(get_current_user),
    use_case=Depends(get_create_category),
):
    return await use_case.execute(CreateCategoryCommand(name=body.name))


@router.patch("/{category_id}", response_model=Category)
async def update_category(
    category_id: int,
    body: CategoryPatch,
    _user=Depends(get_current_user),
    use_case=Depends(get_update_category),
):
    try:
        return await use_case.execute(
            UpdateCategoryCommand(
                category_id=category_id,
                name=body.name,
                is_active=body.is_active,
            )
        )
    except DomainError as exc:
        raise domain_exception_handler(exc)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_category(
    category_id: int,
    _user=Depends(get_current_user),
    use_case=Depends(get_deactivate_category),
):
    try:
        await use_case.execute(DeactivateCategoryCommand(category_id=category_id))
    except DomainError as exc:
        raise domain_exception_handler(exc)
```

- [ ] **Step 4: Create `src/v2/adapters/primary/bff/routers/reports.py`**

```python
from datetime import date
from decimal import Decimal
from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from src.v2.adapters.primary.bff.deps import (
    get_get_monthly,
    get_get_summary,
    get_current_user,
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
    start: date,
    end: date,
    transaction_type: Literal["income", "outcome"] | None = None,
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
```

- [ ] **Step 5: Create `src/v2/adapters/primary/bff/routers/export.py`**

```python
from datetime import date

from fastapi import APIRouter, Depends
from fastapi.responses import Response

from src.v2.adapters.primary.bff.deps import get_export_csv, get_current_user
from src.v2.domain.use_cases.reports.export_csv import ExportCsvQuery

router = APIRouter(prefix="/api/v2/export", tags=["v2-export"])


@router.get("/csv")
async def export_csv(
    start: date,
    end: date,
    _user=Depends(get_current_user),
    use_case=Depends(get_export_csv),
):
    content = await use_case.execute(ExportCsvQuery(start=start, end=end))
    filename = f"expenses_{start}_{end}.csv"
    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
```

- [ ] **Step 6: Run category tests — expect PASS**

```bash
pytest tests/v2/adapters/test_bff_categories.py -v
```

Expected: `5 passed`

- [ ] **Step 7: Commit**

```bash
git add src/v2/adapters/primary/bff/routers/ tests/v2/adapters/test_bff_categories.py
git commit -m "feat(v2): add BFF categories, reports, and export routers"
```

---

## Task 18: Telegram primary adapters

**Files:**
- Create: `src/v2/adapters/primary/telegram/webhook.py`
- Create: `src/v2/adapters/primary/telegram/handlers/message.py`
- Create: `src/v2/adapters/primary/telegram/handlers/commands.py`
- Create: `src/v2/adapters/primary/telegram/handlers/callback.py`

These handlers are thin — they parse Telegram payloads and call use cases. No business logic lives here.

- [ ] **Step 1: Create `src/v2/adapters/primary/telegram/handlers/message.py`**

```python
import base64
import logging

from src.v2.domain.use_cases.telegram.process_message import (
    ProcessMessage,
    ProcessMessageCommand,
)

logger = logging.getLogger(__name__)


async def handle_message(update: dict, use_cases) -> None:
    """Route incoming Telegram messages to the ProcessMessage use case."""
    message = update.get("message") or update.get("edited_message") or {}
    chat_id: int = message.get("chat", {}).get("id")
    message_id: int = message.get("message_id")

    if not chat_id:
        return

    process_message: ProcessMessage = use_cases.process_message

    # Image
    if photos := message.get("photo"):
        largest = max(photos, key=lambda p: p.get("file_size", 0))
        file_id = largest["file_id"]
        image_b64 = await _download_image_b64(file_id)
        if image_b64:
            await process_message.execute(
                ProcessMessageCommand(
                    chat_id=chat_id,
                    entry_type="image",
                    image_b64=image_b64,
                    message_id=message_id,
                )
            )
        return

    # Document (PDF)
    if document := message.get("document"):
        mime = document.get("mime_type", "")
        if "pdf" in mime:
            await _handle_pdf(chat_id, message_id, document, process_message)
        else:
            await use_cases.process_message._notifier.send_message(
                chat_id, "Apenas arquivos PDF são suportados."
            )
        return

    # Text
    if text := message.get("text", "").strip():
        await process_message.execute(
            ProcessMessageCommand(
                chat_id=chat_id,
                entry_type="text",
                text=text,
                message_id=message_id,
            )
        )


async def _download_image_b64(file_id: str) -> str | None:
    """Download a Telegram file and return it as base64."""
    try:
        from src.services.telegram import get_file_url, download_file
        url = await get_file_url(file_id)
        content = await download_file(url)
        return base64.b64encode(content).decode()
    except Exception:
        logger.exception("Failed to download image file_id=%s", file_id)
        return None


async def _handle_pdf(chat_id: int, message_id: int, document: dict, process_message: ProcessMessage) -> None:
    try:
        from src.services.telegram import get_file_url, download_file
        import pdfplumber
        import io

        file_id = document["file_id"]
        file_size = document.get("file_size", 0)
        if file_size > 10 * 1024 * 1024:
            await process_message._notifier.send_message(
                chat_id, "PDF muito grande (máx 10 MB)."
            )
            return

        url = await get_file_url(file_id)
        content = await download_file(url)

        # Try text extraction
        extracted_text = ""
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            for page in pdf.pages:
                extracted_text += page.extract_text() or ""

        if len(extracted_text.strip()) >= 50:
            await process_message.execute(
                ProcessMessageCommand(
                    chat_id=chat_id,
                    entry_type="pdf",
                    text=extracted_text,
                    message_id=message_id,
                )
            )
        else:
            # Scanned PDF — convert first page to image
            import fitz
            doc = fitz.open(stream=content, filetype="pdf")
            page = doc[0]
            pix = page.get_pixmap(dpi=150)
            image_bytes = pix.tobytes("jpeg")
            image_b64 = base64.b64encode(image_bytes).decode()
            await process_message.execute(
                ProcessMessageCommand(
                    chat_id=chat_id,
                    entry_type="pdf",
                    image_b64=image_b64,
                    message_id=message_id,
                )
            )
    except Exception:
        logger.exception("Failed to process PDF for chat_id=%s", chat_id)
        await process_message._notifier.send_message(
            chat_id, "Não consegui processar o PDF. Tente enviar como imagem ou texto."
        )
```

- [ ] **Step 2: Create `src/v2/adapters/primary/telegram/handlers/commands.py`**

```python
import logging
from datetime import date, timedelta

from src.v2.domain.use_cases.telegram.generate_telegram_report import (
    GenerateTelegramReport,
    GenerateTelegramReportCommand,
)

logger = logging.getLogger(__name__)


async def handle_command(update: dict, use_cases) -> None:
    message = update.get("message") or {}
    chat_id: int = message.get("chat", {}).get("id")
    text: str = message.get("text", "").strip()

    if not chat_id or not text.startswith("/"):
        return

    parts = text.split(maxsplit=1)
    command = parts[0].lstrip("/").split("@")[0].lower()
    args = parts[1].strip() if len(parts) > 1 else ""

    if command == "start":
        await use_cases.process_message._notifier.send_message(
            chat_id,
            "Olá! Envie uma foto de comprovante, PDF ou texto para registrar uma despesa.\n"
            "Use /ajuda para ver todos os comandos.",
        )
    elif command == "ajuda":
        await use_cases.process_message._notifier.send_message(
            chat_id,
            "/relatorio [semana|mes|anterior|MM/AAAA] — relatório de despesas\n"
            "/exportar [semana|mes|anterior|MM/AAAA] — exportar CSV\n"
            "/categorias — listar categorias\n"
            "/categorias add <nome> — adicionar categoria",
        )
    elif command == "relatorio":
        await _handle_report(chat_id, args, use_cases)
    elif command == "exportar":
        await _handle_export(chat_id, args, use_cases)
    elif command == "categorias":
        await _handle_categorias(chat_id, args, use_cases)
    else:
        logger.debug("Unknown command: %s", command)


async def _handle_report(chat_id: int, args: str, use_cases) -> None:
    start, end, label = _parse_period(args)
    generate: GenerateTelegramReport = use_cases.generate_telegram_report
    await generate.execute(
        GenerateTelegramReportCommand(
            chat_id=chat_id,
            period_label=label,
            start=start,
            end=end,
        )
    )


async def _handle_export(chat_id: int, args: str, use_cases) -> None:
    from src.v2.domain.use_cases.reports.export_csv import ExportCsv, ExportCsvQuery
    start, end, label = _parse_period(args)
    export_csv: ExportCsv = use_cases.export_csv
    content = await export_csv.execute(ExportCsvQuery(start=start, end=end))
    filename = f"expenses_{start}_{end}.csv"
    await use_cases.process_message._notifier.send_file(
        chat_id, content, filename, caption=f"Despesas — {label}"
    )


async def _handle_categorias(chat_id: int, args: str, use_cases) -> None:
    if args.lower().startswith("add "):
        name = args[4:].strip()
        if name:
            cat = await use_cases.create_category.execute(
                __import__(
                    "src.v2.domain.use_cases.categories.create_category",
                    fromlist=["CreateCategoryCommand"],
                ).CreateCategoryCommand(name=name)
            )
            await use_cases.process_message._notifier.send_message(
                chat_id, f"Categoria '{cat.name}' adicionada!"
            )
        return

    categories = await use_cases.list_categories.execute()
    names = "\n".join(f"• {c.name}" for c in categories if c.is_active)
    await use_cases.process_message._notifier.send_message(
        chat_id, f"Categorias disponíveis:\n{names}"
    )


def _parse_period(args: str) -> tuple[date, date, str]:
    """Parse period argument string into (start, end, label)."""
    today = date.today()
    args = args.strip().lower()

    if args == "semana":
        start = today - timedelta(days=today.weekday())
        return start, today, "Esta semana"

    if args == "anterior":
        first_this_month = today.replace(day=1)
        end = first_this_month - timedelta(days=1)
        start = end.replace(day=1)
        return start, end, f"{end.strftime('%B %Y').capitalize()}"

    if args == "" or args == "mes":
        start = today.replace(day=1)
        return start, today, today.strftime("%B %Y").capitalize()

    # MM/AAAA
    try:
        month, year = args.split("/")
        m, y = int(month), int(year)
        import calendar
        last_day = calendar.monthrange(y, m)[1]
        start = date(y, m, 1)
        end = date(y, m, last_day)
        return start, end, f"{start.strftime('%B %Y').capitalize()}"
    except (ValueError, AttributeError):
        pass

    # Default: current month
    return today.replace(day=1), today, today.strftime("%B %Y").capitalize()
```

- [ ] **Step 3: Create `src/v2/adapters/primary/telegram/handlers/callback.py`**

```python
import logging

from src.v2.domain.use_cases.telegram.cancel_expense import CancelExpenseCommand
from src.v2.domain.use_cases.telegram.change_category import ChangeCategoryCommand
from src.v2.domain.use_cases.telegram.confirm_expense import ConfirmExpenseCommand

logger = logging.getLogger(__name__)


async def handle_callback(update: dict, use_cases) -> None:
    callback_query = update.get("callback_query", {})
    callback_id: str = callback_query.get("id", "")
    message = callback_query.get("message", {})
    chat_id: int = message.get("chat", {}).get("id")
    message_id: int = message.get("message_id")
    data: str = callback_query.get("data", "")

    notifier = use_cases.process_message._notifier
    await notifier.answer_callback(callback_id)

    if data == "confirm":
        await use_cases.confirm_expense.execute(
            ConfirmExpenseCommand(
                chat_id=chat_id,
                message_id=message_id,
                skip_duplicate_check=False,
            )
        )

    elif data == "force_confirm":
        await use_cases.confirm_expense.execute(
            ConfirmExpenseCommand(
                chat_id=chat_id,
                message_id=message_id,
                skip_duplicate_check=True,
            )
        )

    elif data == "cancel":
        await use_cases.cancel_expense.execute(
            CancelExpenseCommand(chat_id=chat_id, message_id=message_id)
        )

    elif data == "edit_category":
        categories = await use_cases.list_categories.execute()
        from src.v2.domain.ports.notifier_port import NotificationButton
        # Build a keyboard with 2 categories per row
        rows = []
        row = []
        for cat in categories:
            if cat.is_active:
                row.append(
                    NotificationButton(
                        text=cat.name,
                        callback_data=f"set_category:{cat.id}:{cat.name}",
                    )
                )
                if len(row) == 2:
                    rows.append(row)
                    row = []
        if row:
            rows.append(row)
        await notifier.edit_message(
            chat_id, message_id, "Escolha a categoria:", buttons=rows
        )

    elif data.startswith("set_category:"):
        # format: set_category:{id}:{name}
        parts = data.split(":", 2)
        if len(parts) == 3:
            try:
                category_id = int(parts[1])
                category_name = parts[2]
                await use_cases.change_category.execute(
                    ChangeCategoryCommand(
                        chat_id=chat_id,
                        message_id=message_id,
                        new_category=category_name,
                        new_category_id=category_id,
                    )
                )
            except (ValueError, IndexError):
                logger.warning("Malformed set_category callback: %r", data)
    else:
        logger.debug("Unhandled callback data: %r", data)
```

- [ ] **Step 4: Create `src/v2/adapters/primary/telegram/webhook.py`**

```python
import logging

from src.v2.adapters.primary.telegram.handlers.callback import handle_callback
from src.v2.adapters.primary.telegram.handlers.commands import handle_command
from src.v2.adapters.primary.telegram.handlers.message import handle_message

logger = logging.getLogger(__name__)


def _extract_chat_id(update: dict) -> int | None:
    for key in ("message", "edited_message", "channel_post"):
        if key in update:
            return update[key].get("chat", {}).get("id")
    if "callback_query" in update:
        return update["callback_query"].get("message", {}).get("chat", {}).get("id")
    return None


async def handle_update(update: dict, use_cases) -> None:
    """Route a Telegram update to the correct handler."""
    if "callback_query" in update:
        await handle_callback(update, use_cases)
        return

    message = update.get("message") or update.get("edited_message") or {}
    text: str = message.get("text", "")

    if text.startswith("/"):
        await handle_command(update, use_cases)
    else:
        await handle_message(update, use_cases)
```

- [ ] **Step 5: Run arch test — must still pass**

```bash
pytest tests/v2/test_architecture.py -v
```

Expected: `PASSED`

- [ ] **Step 6: Commit**

```bash
git add src/v2/adapters/primary/telegram/
git commit -m "feat(v2): add Telegram primary adapters (handlers + webhook router)"
```

---

## Task 19: Bootstrap

**Files:**
- Create: `src/v2/bootstrap.py`

- [ ] **Step 1: Create `src/v2/bootstrap.py`**

```python
from dataclasses import dataclass

from fastapi import APIRouter

from src.config.settings import settings as _settings
from src.v2.adapters.primary.bff.routers.categories import router as categories_router
from src.v2.adapters.primary.bff.routers.export import router as export_router
from src.v2.adapters.primary.bff.routers.reports import router as reports_router
from src.v2.adapters.primary.bff.routers.transactions import router as transactions_router
from src.v2.adapters.secondary.memory.pending_state_adapter import (
    InMemoryPendingStateAdapter,
)
from src.v2.adapters.secondary.openrouter.llm_adapter import OpenRouterLLMAdapter
from src.v2.adapters.secondary.supabase.category_repository import (
    SupabaseCategoryRepository,
)
from src.v2.adapters.secondary.supabase.expense_repository import (
    SupabaseExpenseRepository,
)
from src.v2.adapters.secondary.telegram_api.notifier_adapter import (
    TelegramNotifierAdapter,
)
from src.v2.domain.use_cases.categories.create_category import CreateCategory
from src.v2.domain.use_cases.categories.deactivate_category import DeactivateCategory
from src.v2.domain.use_cases.categories.list_categories import ListCategories
from src.v2.domain.use_cases.categories.update_category import UpdateCategory
from src.v2.domain.use_cases.expenses.create_expense import CreateExpense
from src.v2.domain.use_cases.expenses.delete_expense import DeleteExpense
from src.v2.domain.use_cases.expenses.get_expense import GetExpense
from src.v2.domain.use_cases.expenses.list_expenses import ListExpenses
from src.v2.domain.use_cases.expenses.update_expense import UpdateExpense
from src.v2.domain.use_cases.reports.export_csv import ExportCsv
from src.v2.domain.use_cases.reports.get_monthly import GetMonthly
from src.v2.domain.use_cases.reports.get_summary import GetSummary
from src.v2.domain.use_cases.telegram.cancel_expense import CancelExpense
from src.v2.domain.use_cases.telegram.change_category import ChangeCategory
from src.v2.domain.use_cases.telegram.confirm_expense import ConfirmExpense
from src.v2.domain.use_cases.telegram.generate_telegram_report import (
    GenerateTelegramReport,
)
from src.v2.domain.use_cases.telegram.process_message import ProcessMessage


@dataclass
class UseCaseContainer:
    # Expenses
    create_expense: CreateExpense
    list_expenses: ListExpenses
    get_expense: GetExpense
    update_expense: UpdateExpense
    delete_expense: DeleteExpense
    # Categories
    list_categories: ListCategories
    create_category: CreateCategory
    update_category: UpdateCategory
    deactivate_category: DeactivateCategory
    # Reports
    get_summary: GetSummary
    get_monthly: GetMonthly
    export_csv: ExportCsv
    # Telegram flows
    process_message: ProcessMessage
    confirm_expense: ConfirmExpense
    cancel_expense: CancelExpense
    change_category: ChangeCategory
    generate_telegram_report: GenerateTelegramReport


def build_use_cases() -> UseCaseContainer:
    """Build and wire all adapters and use cases. Call once at startup."""
    from supabase import acreate_client, AsyncClient
    import asyncio

    # We need an AsyncClient but we're in a sync context at import time.
    # Use a lazy getter that's resolved at first request via lifespan.
    # For simplicity, we create the client synchronously using the sync helper.
    from supabase import create_client
    supabase = create_client(_settings.supabase_url, _settings.supabase_service_key)

    expense_repo = SupabaseExpenseRepository(supabase)
    category_repo = SupabaseCategoryRepository(supabase)
    llm = OpenRouterLLMAdapter(
        model_vision=_settings.model_vision,
        model_fast=_settings.model_fast,
    )
    notifier = TelegramNotifierAdapter(bot_token=_settings.telegram_bot_token)
    pending = InMemoryPendingStateAdapter()

    return UseCaseContainer(
        create_expense=CreateExpense(expense_repo),
        list_expenses=ListExpenses(expense_repo),
        get_expense=GetExpense(expense_repo),
        update_expense=UpdateExpense(expense_repo),
        delete_expense=DeleteExpense(expense_repo),
        list_categories=ListCategories(category_repo),
        create_category=CreateCategory(category_repo),
        update_category=UpdateCategory(category_repo),
        deactivate_category=DeactivateCategory(category_repo),
        get_summary=GetSummary(expense_repo),
        get_monthly=GetMonthly(expense_repo),
        export_csv=ExportCsv(expense_repo),
        process_message=ProcessMessage(llm, category_repo, pending, notifier),
        confirm_expense=ConfirmExpense(expense_repo, llm, pending, notifier),
        cancel_expense=CancelExpense(pending, notifier),
        change_category=ChangeCategory(pending, notifier),
        generate_telegram_report=GenerateTelegramReport(expense_repo, llm, notifier),
    )


def build_v2_router() -> APIRouter:
    """Return an APIRouter with all v2 BFF routes included."""
    router = APIRouter()
    router.include_router(transactions_router)
    router.include_router(categories_router)
    router.include_router(reports_router)
    router.include_router(export_router)
    return router
```

- [ ] **Step 2: Check that `settings` has `model_vision` and `model_fast` fields**

Open `src/config/settings.py` and verify these two fields exist:

```python
model_vision: str = "anthropic/claude-sonnet-4-6"
model_fast: str = "anthropic/claude-haiku-4-5"
```

If they don't exist yet, add them. These map to the existing `settings.model_vision` and `settings.model_fast` used in `src/agents/extractor.py`.

- [ ] **Step 3: Run arch test**

```bash
pytest tests/v2/test_architecture.py -v
```

Expected: `PASSED` — bootstrap.py is NOT in `src.v2.domain`, so it's allowed to import adapters.

- [ ] **Step 4: Commit**

```bash
git add src/v2/bootstrap.py
git commit -m "feat(v2): add bootstrap — wires all adapters and use cases"
```

---

## Task 20: Mount v2 in main.py

**Files:**
- Modify: `src/main.py`

- [ ] **Step 1: Read `src/main.py`** to find the exact lines where v1 routers are included

The relevant block currently reads:
```python
app.include_router(transactions.router)
app.include_router(expenses.router)
app.include_router(categories.router)
app.include_router(reports.router)
app.include_router(export.router)
```

- [ ] **Step 2: Add the v2 router inclusion and use-case wiring to `src/main.py`**

Add these imports at the top of `src/main.py`, after the existing imports:

```python
from src.v2.bootstrap import build_use_cases, build_v2_router
```

Add this block inside the `lifespan` function, before `yield`:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    from src.scheduler.reports import start_scheduler, stop_scheduler
    # Wire v2 use cases
    app.state.use_cases = build_use_cases()
    start_scheduler()
    yield
    stop_scheduler()
```

Add v2 router inclusion after the existing `app.include_router(export.router)` line:

```python
# v2 — new hexagonal architecture (routes at /api/v2/...)
app.include_router(build_v2_router())
```

- [ ] **Step 3: Update the `/webhook` endpoint to delegate to the v2 Telegram handler**

Find the existing `webhook` function in `src/main.py`. Replace the `await handle_update(update)` call with the v2 handler:

```python
    try:
        # v2 Telegram handler
        from src.v2.adapters.primary.telegram.webhook import handle_update as handle_update_v2
        await handle_update_v2(update, app.state.use_cases)
    except Exception:
        logger.exception("Error processing update: %s", update)
```

Keep the `handle_update` import from v1 temporarily commented out (not deleted) until v2 is validated:

```python
# from src.handlers.message import handle_update  # v1 — kept for reference
```

- [ ] **Step 4: Start the dev server and verify it boots without errors**

```bash
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

Expected output (no errors):
```
INFO:     Application startup complete.
```

Stop the server with `Ctrl+C`.

- [ ] **Step 5: Run the full test suite**

```bash
pytest tests/ -v --tb=short
```

Expected: existing v1 tests pass, all v2 tests pass.

- [ ] **Step 6: Smoke test the v2 API**

With the dev server running, send a request to a v2 endpoint (requires a valid Supabase JWT in `$TOKEN`):

```bash
curl -s -H "Authorization: Bearer $TOKEN" \
     http://localhost:8000/api/v2/categories | python -m json.tool
```

Expected: a JSON array of categories.

- [ ] **Step 7: Commit**

```bash
git add src/main.py
git commit -m "feat(v2): mount v2 routers and Telegram handler in main.py"
```

---

## Task 21: Final validation

- [ ] **Step 1: Run full test suite**

```bash
pytest tests/ -v
```

Expected: all tests pass, `0 failed`.

- [ ] **Step 2: Verify all architecture contracts pass**

```bash
pytest tests/v2/test_architecture.py -v -s
```

Expected:
```
PASSED tests/v2/test_architecture.py::test_hexagonal_contracts
  ✓ Domain must not import from adapters
  ✓ Secondary adapters must not import from primary adapters
  ✓ Entities and ports must not import from use_cases
```

- [ ] **Step 3: Verify v2 routes are accessible**

```bash
curl -s http://localhost:8000/health
```

Expected: `{"status": "ok"}`

```bash
# List available routes (OpenAPI disabled in prod, so check programmatically)
python -c "
from src.main import app
v2_routes = [r.path for r in app.routes if '/v2/' in getattr(r, 'path', '')]
print('\n'.join(sorted(v2_routes)))
"
```

Expected output:
```
/api/v2/categories
/api/v2/categories/{category_id}
/api/v2/export/csv
/api/v2/reports/monthly
/api/v2/reports/summary
/api/v2/transactions
/api/v2/transactions/{transaction_id}
```

- [ ] **Step 4: Final commit**

```bash
git add .
git commit -m "feat(v2): hexagonal architecture complete — all contracts enforced, all tests green"
```

---

## Phase 4 complete

The v2 hexagonal architecture is live alongside v1. The frontend can now migrate endpoint by endpoint from `/api/...` to `/api/v2/...`.

**Migration checklist (frontend side):**
- [ ] Update `NEXT_PUBLIC_API_BASE_URL` calls in `src/lib/api.ts` from `/api/transactions` → `/api/v2/transactions`
- [ ] Update `/api/categories` → `/api/v2/categories`
- [ ] Update `/api/reports/summary` and `/api/reports/monthly` → `/api/v2/reports/...`
- [ ] Update `/api/export/csv` → `/api/v2/export/csv`
- [ ] Once all endpoints are migrated: delete v1 routers and remove `src.handlers`, `src.agents`, `src.services.database` references from the main flow

**Spec:** `docs/superpowers/specs/2026-04-11-hexagonal-architecture-design.md`
