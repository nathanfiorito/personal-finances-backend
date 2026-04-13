# BFF Endpoints Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace 3 + 2 parallel frontend HTTP calls with two dedicated BFF endpoints (`GET /api/v2/bff/dashboard` and `GET /api/v2/bff/expenses`), and remove the four redundant read-only endpoints they replace.

**Architecture:** Two new FastAPI routers in `src/v2/adapters/primary/bff/routers/` compose existing use cases via `asyncio.gather` — no new domain logic or ports. Both routers are registered in `bootstrap.py`. The frontend's `api.ts`, `dashboard/page.tsx`, `expenses/page.tsx`, and `ExpenseModal.tsx` are updated to use the new endpoints; the `ExpenseModal` receives `categories` as a prop instead of fetching them independently.

**Tech Stack:** Python 3.12 / FastAPI / pytest / asyncio — TypeScript / Next.js 15 App Router / Vitest

---

## File Map

**Create (backend):**
- `src/v2/adapters/primary/bff/routers/bff_dashboard.py`
- `src/v2/adapters/primary/bff/routers/bff_expenses.py`
- `tests/v2/adapters/test_bff_dashboard.py`
- `tests/v2/adapters/test_bff_expenses.py`

**Modify (backend):**
- `src/v2/bootstrap.py` — register two new routers
- `src/v2/adapters/primary/bff/routers/transactions.py` — remove `GET ""` and `GET "/{id}"`
- `src/v2/adapters/primary/bff/routers/categories.py` — remove `GET ""`
- `src/v2/adapters/primary/bff/routers/reports.py` — remove `GET "/summary"`
- `tests/v2/adapters/test_bff_transactions.py` — remove tests for deleted routes
- `tests/v2/adapters/test_bff_categories.py` — remove test for deleted route
- `tests/v2/adapters/test_bff_reports_export.py` — remove `TestSummary` class
- `docs/API.md` — reflect new endpoints and removals

**Modify (frontend — `personal-finances-frontend/`):**
- `src/lib/api.ts` — add `BffDashboardResponse`, `BffExpensesResponse`, `getBffExpenses`; remove `getExpenses`, `getExpense`, `getCategories`, `getSummary`
- `src/app/(protected)/dashboard/page.tsx` — replace 3 fetches with 1
- `src/app/(protected)/expenses/page.tsx` — use `getBffExpenses`, pass `categories` to modal
- `src/components/expenses/ExpenseModal.tsx` — accept `categories` prop, remove internal fetch
- `src/test/api.test.ts` — remove old tests, add `getBffExpenses` tests
- `src/test/ExpenseModal.test.tsx` — remove `getCategories` mock, pass `categories` as prop

---

## Task 1: BFF Dashboard Router

**Files:**
- Create: `tests/v2/adapters/test_bff_dashboard.py`
- Create: `src/v2/adapters/primary/bff/routers/bff_dashboard.py`

- [ ] **Step 1: Write the failing test**

Create `tests/v2/adapters/test_bff_dashboard.py`:

```python
from decimal import Decimal
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.v2.adapters.primary.bff.routers.bff_dashboard import router
from src.v2.domain.use_cases.reports.get_summary import SummaryItem


def _app(use_cases: SimpleNamespace) -> FastAPI:
    app = FastAPI()
    app.state.use_cases = use_cases
    from src.v2.adapters.primary.bff import deps
    app.dependency_overrides[deps.get_current_user] = lambda: {"sub": "test-user"}
    app.include_router(router)
    return app


class StubGetSummary:
    async def execute(self, query):
        return [SummaryItem(category="Alimentação", total=Decimal("245.90"))]


class StubListExpenses:
    def __init__(self, total: int = 5):
        self._total = total

    async def execute(self, query):
        return [], self._total


def _default_uc():
    return SimpleNamespace(
        get_summary=StubGetSummary(),
        list_expenses=StubListExpenses(total=5),
    )


def test_dashboard_returns_200_with_aggregated_data():
    client = TestClient(_app(_default_uc()))
    resp = client.get("/api/v2/bff/dashboard?start=2026-01-01&end=2026-01-31")
    assert resp.status_code == 200
    body = resp.json()
    assert "outcome_summary" in body
    assert "income_summary" in body
    assert body["transaction_count"] == 5
    assert body["outcome_summary"][0]["category"] == "Alimentação"
    assert body["outcome_summary"][0]["total"] == "245.90"


def test_dashboard_requires_start_and_end():
    client = TestClient(_app(_default_uc()))
    resp = client.get("/api/v2/bff/dashboard?start=2026-01-01")
    assert resp.status_code == 422


def test_dashboard_returns_422_when_start_after_end():
    client = TestClient(_app(_default_uc()))
    resp = client.get("/api/v2/bff/dashboard?start=2026-02-01&end=2026-01-01")
    assert resp.status_code == 422
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd personal-finances-backend
pytest tests/v2/adapters/test_bff_dashboard.py -v
```

Expected: `ImportError` — `bff_dashboard` module does not exist yet.

- [ ] **Step 3: Implement the router**

Create `src/v2/adapters/primary/bff/routers/bff_dashboard.py`:

```python
import asyncio
from datetime import date as _date

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from src.v2.adapters.primary.bff.deps import (
    get_current_user,
    get_get_summary,
    get_list_expenses,
)
from src.v2.domain.use_cases.expenses.list_expenses import ListExpensesQuery
from src.v2.domain.use_cases.reports.get_summary import GetSummaryQuery

router = APIRouter(prefix="/api/v2/bff", tags=["v2-bff"])


class SummaryItemOut(BaseModel):
    category: str
    total: str


class DashboardResponse(BaseModel):
    outcome_summary: list[SummaryItemOut]
    income_summary: list[SummaryItemOut]
    transaction_count: int


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(
    start: _date,
    end: _date,
    _user=Depends(get_current_user),
    summary_uc=Depends(get_get_summary),
    list_uc=Depends(get_list_expenses),
):
    if start > end:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="start must be <= end",
        )
    outcome_items, income_items, list_result = await asyncio.gather(
        summary_uc.execute(GetSummaryQuery(start=start, end=end, transaction_type="outcome")),
        summary_uc.execute(GetSummaryQuery(start=start, end=end, transaction_type="income")),
        list_uc.execute(ListExpensesQuery(start=start, end=end, page=1, page_size=1)),
    )
    _, total = list_result
    return DashboardResponse(
        outcome_summary=[
            SummaryItemOut(category=i.category, total=str(i.total)) for i in outcome_items
        ],
        income_summary=[
            SummaryItemOut(category=i.category, total=str(i.total)) for i in income_items
        ],
        transaction_count=total,
    )
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/v2/adapters/test_bff_dashboard.py -v
```

Expected: 3 PASSED.

- [ ] **Step 5: Commit**

```bash
git add src/v2/adapters/primary/bff/routers/bff_dashboard.py tests/v2/adapters/test_bff_dashboard.py
git commit -m "feat: add GET /api/v2/bff/dashboard endpoint"
```

---

## Task 2: BFF Expenses Router

**Files:**
- Create: `tests/v2/adapters/test_bff_expenses.py`
- Create: `src/v2/adapters/primary/bff/routers/bff_expenses.py`

- [ ] **Step 1: Write the failing test**

Create `tests/v2/adapters/test_bff_expenses.py`:

```python
import datetime as _dt
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.v2.adapters.primary.bff.routers.bff_expenses import router
from src.v2.domain.entities.category import Category
from src.v2.domain.entities.expense import Expense


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
    from src.v2.adapters.primary.bff import deps
    app.dependency_overrides[deps.get_current_user] = lambda: {"sub": "test-user"}
    app.include_router(router)
    return app


class StubListExpenses:
    async def execute(self, query):
        return [_make_expense()], 1


class StubListCategories:
    async def execute(self):
        return [Category(id=1, name="Alimentação", is_active=True)]


def _default_uc():
    return SimpleNamespace(
        list_expenses=StubListExpenses(),
        list_categories=StubListCategories(),
    )


def test_expenses_page_returns_200_with_transactions_and_categories():
    client = TestClient(_app(_default_uc()))
    resp = client.get("/api/v2/bff/expenses")
    assert resp.status_code == 200
    body = resp.json()
    assert "transactions" in body
    assert "categories" in body
    assert body["transactions"]["total"] == 1
    assert len(body["transactions"]["items"]) == 1
    assert len(body["categories"]) == 1
    assert body["categories"][0]["name"] == "Alimentação"


def test_expenses_page_passes_filters_to_list_uc():
    received = {}

    class CapturingListExpenses:
        async def execute(self, query):
            received["query"] = query
            return [], 0

    uc = SimpleNamespace(
        list_expenses=CapturingListExpenses(),
        list_categories=StubListCategories(),
    )
    client = TestClient(_app(uc))
    client.get("/api/v2/bff/expenses?category_id=2&page=2&page_size=10")
    assert received["query"].category_id == 2
    assert received["query"].page == 2
    assert received["query"].page_size == 10
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/v2/adapters/test_bff_expenses.py -v
```

Expected: `ImportError` — `bff_expenses` module does not exist yet.

- [ ] **Step 3: Implement the router**

Create `src/v2/adapters/primary/bff/routers/bff_expenses.py`:

```python
import asyncio
from datetime import date as _date
from typing import Literal

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel

from src.v2.adapters.primary.bff.deps import (
    get_current_user,
    get_list_categories,
    get_list_expenses,
)
from src.v2.domain.entities.category import Category
from src.v2.domain.entities.expense import Expense
from src.v2.domain.use_cases.expenses.list_expenses import ListExpensesQuery

router = APIRouter(prefix="/api/v2/bff", tags=["v2-bff"])


class TransactionPage(BaseModel):
    items: list[Expense]
    total: int
    page: int
    page_size: int


class ExpensesPageResponse(BaseModel):
    transactions: TransactionPage
    categories: list[Category]


@router.get("/expenses", response_model=ExpensesPageResponse)
async def get_expenses_page(
    start: _date | None = None,
    end: _date | None = None,
    category_id: int | None = None,
    transaction_type: Literal["income", "outcome"] | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    _user=Depends(get_current_user),
    list_uc=Depends(get_list_expenses),
    categories_uc=Depends(get_list_categories),
):
    (items, total), categories = await asyncio.gather(
        list_uc.execute(
            ListExpensesQuery(
                start=start,
                end=end,
                category_id=category_id,
                transaction_type=transaction_type,
                page=page,
                page_size=page_size,
            )
        ),
        categories_uc.execute(),
    )
    return ExpensesPageResponse(
        transactions=TransactionPage(items=items, total=total, page=page, page_size=page_size),
        categories=categories,
    )
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/v2/adapters/test_bff_expenses.py -v
```

Expected: 2 PASSED.

- [ ] **Step 5: Commit**

```bash
git add src/v2/adapters/primary/bff/routers/bff_expenses.py tests/v2/adapters/test_bff_expenses.py
git commit -m "feat: add GET /api/v2/bff/expenses endpoint"
```

---

## Task 3: Register New Routers in Bootstrap

**Files:**
- Modify: `src/v2/bootstrap.py`

- [ ] **Step 1: Update bootstrap.py**

Add these two imports at the top of `src/v2/bootstrap.py` alongside the existing router imports:

```python
from src.v2.adapters.primary.bff.routers.bff_dashboard import router as bff_dashboard_router
from src.v2.adapters.primary.bff.routers.bff_expenses import router as bff_expenses_router
```

Update `build_v2_router()` to include them:

```python
def build_v2_router() -> APIRouter:
    """Return an APIRouter with all v2 BFF routes included."""
    router = APIRouter()
    router.include_router(transactions_router)
    router.include_router(categories_router)
    router.include_router(reports_router)
    router.include_router(export_router)
    router.include_router(bff_dashboard_router)
    router.include_router(bff_expenses_router)
    return router
```

- [ ] **Step 2: Run all v2 tests to verify nothing is broken**

```bash
pytest tests/v2/ -v
```

Expected: all existing tests still PASS, plus the 5 new tests from Tasks 1–2.

- [ ] **Step 3: Commit**

```bash
git add src/v2/bootstrap.py
git commit -m "feat: register BFF dashboard and expenses routers"
```

---

## Task 4: Remove Redundant GET Endpoints

**Files:**
- Modify: `src/v2/adapters/primary/bff/routers/transactions.py`
- Modify: `src/v2/adapters/primary/bff/routers/categories.py`
- Modify: `src/v2/adapters/primary/bff/routers/reports.py`
- Modify: `tests/v2/adapters/test_bff_transactions.py`
- Modify: `tests/v2/adapters/test_bff_categories.py`
- Modify: `tests/v2/adapters/test_bff_reports_export.py`

- [ ] **Step 1: Replace transactions.py — remove list and get-by-id handlers**

Replace the full content of `src/v2/adapters/primary/bff/routers/transactions.py` with:

```python
from datetime import date as _date
from decimal import Decimal
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, field_validator

from src.v2.adapters.primary.bff.deps import (
    domain_exception_handler,
    get_create_expense,
    get_current_user,
    get_delete_expense,
    get_update_expense,
)
from src.v2.domain.entities.expense import Expense
from src.v2.domain.exceptions import DomainError
from src.v2.domain.use_cases.expenses.create_expense import CreateExpenseCommand
from src.v2.domain.use_cases.expenses.delete_expense import DeleteExpenseCommand
from src.v2.domain.use_cases.expenses.update_expense import UpdateExpenseCommand

router = APIRouter(prefix="/api/v2/transactions", tags=["v2-transactions"])


class TransactionCreate(BaseModel):
    amount: Decimal
    date: _date | None = None
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
    date: _date | None = None
    category_id: int | None = None
    entry_type: str | None = None
    transaction_type: Literal["income", "outcome"] | None = None
    establishment: str | None = None
    description: str | None = None
    tax_id: str | None = None


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

- [ ] **Step 2: Replace categories.py — remove list handler**

Replace the full content of `src/v2/adapters/primary/bff/routers/categories.py` with:

```python
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel

from src.v2.adapters.primary.bff.deps import (
    domain_exception_handler,
    get_create_category,
    get_current_user,
    get_deactivate_category,
    get_update_category,
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

- [ ] **Step 3: Replace reports.py — remove summary handler**

Replace the full content of `src/v2/adapters/primary/bff/routers/reports.py` with:

```python
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
```

- [ ] **Step 4: Replace test_bff_transactions.py — remove tests for deleted routes**

Replace the full content of `tests/v2/adapters/test_bff_transactions.py` with:

```python
import datetime as _dt
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

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
    from src.v2.adapters.primary.bff import deps
    app.dependency_overrides[deps.get_current_user] = lambda: {"sub": "test-user"}
    app.include_router(router)
    return app


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


def test_create_transaction_returns_201():
    uc = SimpleNamespace(
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


def test_update_transaction_returns_404_when_not_found():
    uc = SimpleNamespace(
        create_expense=StubCreateExpense(),
        update_expense=StubUpdateExpense(found=False),
        delete_expense=StubDeleteExpense(),
    )
    client = TestClient(_app(uc))
    resp = client.put(
        f"/api/v2/transactions/{uuid4()}",
        json={"amount": "10.00"},
    )
    assert resp.status_code == 404


def test_delete_transaction_returns_204():
    expense = _make_expense()

    class DeleteStub:
        async def execute(self, cmd):
            pass

    uc = SimpleNamespace(
        create_expense=StubCreateExpense(),
        update_expense=StubUpdateExpense(),
        delete_expense=DeleteStub(),
    )
    client = TestClient(_app(uc))
    resp = client.delete(f"/api/v2/transactions/{expense.id}")
    assert resp.status_code == 204
```

- [ ] **Step 5: Replace test_bff_categories.py — remove list test**

Replace the full content of `tests/v2/adapters/test_bff_categories.py` with:

```python
from types import SimpleNamespace

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
        create_category=StubCreateCategory(),
        update_category=StubUpdateCategory(),
        deactivate_category=StubDeactivateCategory(),
    )


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

- [ ] **Step 6: Replace test_bff_reports_export.py — remove TestSummary**

Replace the full content of `tests/v2/adapters/test_bff_reports_export.py` with:

```python
from decimal import Decimal
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.v2.adapters.primary.bff.routers.export import router as export_router
from src.v2.adapters.primary.bff.routers.reports import router as reports_router
from src.v2.domain.use_cases.reports.get_monthly import MonthlyByCategoryItem, MonthlyItem


def _app(use_cases: SimpleNamespace) -> FastAPI:
    app = FastAPI()
    app.state.use_cases = use_cases
    from src.v2.adapters.primary.bff import deps
    app.dependency_overrides[deps.get_current_user] = lambda: {"sub": "test-user"}
    app.include_router(reports_router)
    app.include_router(export_router)
    return app


class StubGetMonthly:
    async def execute(self, query):
        return [
            MonthlyItem(
                month=1,
                total=Decimal("369.40"),
                by_category=[
                    MonthlyByCategoryItem(category="Alimentação", total=Decimal("245.90")),
                ],
            )
        ]


class StubExportCsv:
    async def execute(self, query):
        return b"\xef\xbb\xbfdate,amount\n2024-01-15,50.00\n"


def _default_uc():
    return SimpleNamespace(
        get_monthly=StubGetMonthly(),
        export_csv=StubExportCsv(),
    )


class TestMonthly:
    def test_returns_200_with_monthly_items(self):
        client = TestClient(_app(_default_uc()))
        resp = client.get("/api/v2/reports/monthly?year=2024")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["month"] == 1
        assert data[0]["total"] == "369.40"
        assert data[0]["by_category"][0]["category"] == "Alimentação"

    def test_requires_year(self):
        client = TestClient(_app(_default_uc()))
        resp = client.get("/api/v2/reports/monthly")
        assert resp.status_code == 422


class TestExportCsv:
    def test_returns_csv_content(self):
        client = TestClient(_app(_default_uc()))
        resp = client.get("/api/v2/export/csv?start=2024-01-01&end=2024-01-31")
        assert resp.status_code == 200
        assert "text/csv" in resp.headers["content-type"]
        assert "attachment" in resp.headers["content-disposition"]
        assert "expenses_2024-01-01_2024-01-31.csv" in resp.headers["content-disposition"]

    def test_requires_start_and_end(self):
        client = TestClient(_app(_default_uc()))
        resp = client.get("/api/v2/export/csv?start=2024-01-01")
        assert resp.status_code == 422
```

- [ ] **Step 7: Run all v2 tests to verify suite is clean**

```bash
pytest tests/v2/ -v
```

Expected: all tests PASS, no references to removed routes.

- [ ] **Step 8: Commit**

```bash
git add src/v2/adapters/primary/bff/routers/transactions.py \
        src/v2/adapters/primary/bff/routers/categories.py \
        src/v2/adapters/primary/bff/routers/reports.py \
        tests/v2/adapters/test_bff_transactions.py \
        tests/v2/adapters/test_bff_categories.py \
        tests/v2/adapters/test_bff_reports_export.py
git commit -m "refactor: remove redundant GET list endpoints replaced by BFF"
```

---

## Task 5: Update API Docs

**Files:**
- Modify: `docs/API.md`

- [ ] **Step 1: Update the BFF section**

In `docs/API.md`, under `## REST API — Frontend`, replace the **Transactions** and **Categories** sections with the following. Also update the **Reports** section and add the new **BFF** section.

Remove these entries entirely:
- `GET /api/v2/transactions` (list with filters)
- `GET /api/v2/transactions/{id}`
- `GET /api/v2/categories`
- `GET /api/v2/reports/summary`

Add a new `### BFF — Page Endpoints` section after the existing sections:

```markdown
### BFF — Page Endpoints — `src/v2/adapters/primary/bff/routers/bff_dashboard.py`, `bff_expenses.py`

These endpoints aggregate data for a specific frontend page in a single request.

#### `GET /api/v2/bff/dashboard`

Returns everything the Dashboard page needs in one call.

**Required query params:** `start`, `end` (`YYYY-MM-DD`)

**Response `200 OK`:**
```json
{
  "outcome_summary": [{ "category": "Alimentação", "total": "245.90" }],
  "income_summary":  [{ "category": "Salário",     "total": "5000.00" }],
  "transaction_count": 42
}
```

**Response `422`:** `start > end`

---

#### `GET /api/v2/bff/expenses`

Returns paginated transactions and the full active category list for the Expenses page.

**Query params:** same filters as the old `GET /api/v2/transactions` (`start`, `end`, `category_id`, `transaction_type`, `page`, `page_size`)

**Response `200 OK`:**
```json
{
  "transactions": { "items": [...], "total": 42, "page": 1, "page_size": 20 },
  "categories":   [{ "id": 1, "name": "Alimentação", "is_active": true }]
}
```
```

- [ ] **Step 2: Commit**

```bash
git add docs/API.md
git commit -m "docs: update API.md for BFF endpoints and removed routes"
```

---

## Task 6: Frontend — api.ts

**Files:**
- Modify: `src/lib/api.ts` (frontend repo)
- Modify: `src/test/api.test.ts` (frontend repo)

All commands in this task run from the `personal-finances-frontend/` directory.

- [ ] **Step 1: Add BFF types and getBffExpenses, remove obsolete functions**

Replace the full content of `src/lib/api.ts` with:

```typescript
"use client";

import { createClient } from "@/lib/supabase/client";

export interface Expense {
  id: string;
  amount: string;
  date: string;
  establishment: string | null;
  description: string | null;
  category: string;
  category_id: number | null;
  tax_id: string | null;
  entry_type: string;
  transaction_type: "income" | "outcome";
  confidence: number | null;
  created_at: string;
}

export interface CategoryOut {
  id: number;
  name: string;
  is_active: boolean;
}

export interface SummaryItem {
  category: string;
  total: string;
}

export interface MonthlyItem {
  month: number;
  total: string;
  by_category: { category: string; total: string }[];
}

export interface PaginatedExpenses {
  items: Expense[];
  total: number;
  page: number;
  page_size: number;
}

export interface ExpenseFilters {
  start?: string;
  end?: string;
  category_id?: number;
  transaction_type?: "income" | "outcome";
  page?: number;
  page_size?: number;
}

export interface ExpenseInput {
  amount: number;
  date: string;
  establishment?: string;
  description?: string;
  category_id?: number;
  entry_type: string;
  transaction_type: "income" | "outcome";
}

export interface BffDashboardResponse {
  outcome_summary: SummaryItem[];
  income_summary: SummaryItem[];
  transaction_count: number;
}

export interface BffExpensesResponse {
  transactions: PaginatedExpenses;
  categories: CategoryOut[];
}

async function getJwt(): Promise<string | null> {
  const supabase = createClient();
  const { data } = await supabase.auth.getSession();
  return data.session?.access_token ?? null;
}

async function apiFetch<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const jwt = await getJwt();
  const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string> | undefined),
  };

  if (jwt) {
    headers["Authorization"] = `Bearer ${jwt}`;
  }

  const response = await fetch(`${baseUrl}${path}`, {
    ...options,
    headers,
  });

  if (response.status === 401 || response.status === 403) {
    const supabase = createClient();
    await supabase.auth.signOut();
    window.location.href = "/login";
    throw new Error("Unauthorized");
  }

  if (!response.ok) {
    let errorMessage = `HTTP ${response.status}`;
    try {
      const body = await response.json();
      errorMessage = body.detail || body.message || errorMessage;
    } catch {
      // ignore parse error
    }
    throw new Error(errorMessage);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

// ─── Transactions (write) ────────────────────────────────────────────────────

export async function createExpense(data: ExpenseInput): Promise<Expense> {
  return apiFetch<Expense>("/api/v2/transactions", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function updateExpense(id: string, data: Partial<ExpenseInput>): Promise<Expense> {
  return apiFetch<Expense>(`/api/v2/transactions/${id}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

export async function deleteExpense(id: string): Promise<void> {
  return apiFetch<void>(`/api/v2/transactions/${id}`, { method: "DELETE" });
}

// ─── Categories (write) ──────────────────────────────────────────────────────

export async function createCategory(name: string): Promise<CategoryOut> {
  return apiFetch<CategoryOut>("/api/v2/categories", {
    method: "POST",
    body: JSON.stringify({ name }),
  });
}

export async function updateCategory(id: number, data: Partial<CategoryOut>): Promise<CategoryOut> {
  return apiFetch<CategoryOut>(`/api/v2/categories/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export async function deactivateCategory(id: number): Promise<void> {
  return apiFetch<void>(`/api/v2/categories/${id}`, { method: "DELETE" });
}

// ─── Reports ─────────────────────────────────────────────────────────────────

export async function getMonthly(year: number): Promise<MonthlyItem[]> {
  return apiFetch<MonthlyItem[]>(`/api/v2/reports/monthly?year=${year}`);
}

// ─── Export ──────────────────────────────────────────────────────────────────

export async function exportCsv(start: string, end: string): Promise<Blob> {
  const jwt = await getJwt();
  const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;

  const response = await fetch(`${baseUrl}/api/v2/export/csv?start=${start}&end=${end}`, {
    headers: jwt ? { Authorization: `Bearer ${jwt}` } : {},
  });

  if (response.status === 401 || response.status === 403) {
    const supabase = createClient();
    await supabase.auth.signOut();
    window.location.href = "/login";
    throw new Error("Unauthorized");
  }

  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.blob();
}

// ─── BFF ─────────────────────────────────────────────────────────────────────

export async function getBffExpenses(filters: ExpenseFilters = {}): Promise<BffExpensesResponse> {
  const params = new URLSearchParams();
  if (filters.start) params.set("start", filters.start);
  if (filters.end) params.set("end", filters.end);
  if (filters.category_id !== undefined) params.set("category_id", String(filters.category_id));
  if (filters.transaction_type) params.set("transaction_type", filters.transaction_type);
  if (filters.page !== undefined) params.set("page", String(filters.page));
  if (filters.page_size !== undefined) params.set("page_size", String(filters.page_size));

  const query = params.toString() ? `?${params.toString()}` : "";
  return apiFetch<BffExpensesResponse>(`/api/v2/bff/expenses${query}`);
}
```

- [ ] **Step 2: Update api.test.ts — replace tests for removed functions**

Replace the full content of `src/test/api.test.ts` with:

```typescript
import { describe, it, expect, vi, beforeEach } from "vitest";

vi.mock("@/lib/supabase/client", () => ({
  createClient: () => ({
    auth: {
      getSession: vi.fn().mockResolvedValue({
        data: { session: { access_token: "test-jwt" } },
      }),
      signOut: vi.fn().mockResolvedValue({}),
    },
  }),
}));

import {
  createExpense,
  updateExpense,
  deleteExpense,
  getMonthly,
  getBffExpenses,
} from "@/lib/api";

function mockFetch(status: number, body: unknown = {}) {
  const response = {
    ok: status >= 200 && status < 300,
    status,
    json: vi.fn().mockResolvedValue(body),
    blob: vi.fn(),
  };
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(response));
  return response;
}

function capturedUrl(): string {
  const calls = (fetch as ReturnType<typeof vi.fn>).mock.calls;
  return calls[calls.length - 1][0] as string;
}

beforeEach(() => {
  vi.unstubAllGlobals();
  process.env.NEXT_PUBLIC_API_BASE_URL = "http://api.test";
});

const emptyBffExpenses = {
  transactions: { items: [], total: 0, page: 1, page_size: 20 },
  categories: [],
};

// ─── Route paths ─────────────────────────────────────────────────────────────

describe("route paths", () => {
  it("createExpense POSTs to /api/v2/transactions", async () => {
    mockFetch(201, {});
    await createExpense({ amount: 50, date: "2025-03-01", entry_type: "texto", transaction_type: "outcome" });
    expect(capturedUrl()).toBe("http://api.test/api/v2/transactions");
  });

  it("updateExpense PUTs to /api/v2/transactions/{id}", async () => {
    mockFetch(200, {});
    await updateExpense("abc-123", { transaction_type: "income" });
    expect(capturedUrl()).toBe("http://api.test/api/v2/transactions/abc-123");
  });

  it("deleteExpense DELETEs /api/v2/transactions/{id}", async () => {
    mockFetch(204);
    await deleteExpense("abc-123");
    expect(capturedUrl()).toBe("http://api.test/api/v2/transactions/abc-123");
  });

  it("getBffExpenses calls /api/v2/bff/expenses", async () => {
    mockFetch(200, emptyBffExpenses);
    await getBffExpenses();
    expect(capturedUrl()).toContain("/api/v2/bff/expenses");
  });
});

// ─── getBffExpenses — query params ───────────────────────────────────────────

describe("getBffExpenses — query params", () => {
  it("no filters → no query string", async () => {
    mockFetch(200, emptyBffExpenses);
    await getBffExpenses();
    expect(capturedUrl()).toBe("http://api.test/api/v2/bff/expenses");
  });

  it("transaction_type=income is appended", async () => {
    mockFetch(200, emptyBffExpenses);
    await getBffExpenses({ transaction_type: "income" });
    expect(capturedUrl()).toContain("transaction_type=income");
  });

  it("undefined transaction_type is not appended", async () => {
    mockFetch(200, emptyBffExpenses);
    await getBffExpenses({ transaction_type: undefined });
    expect(capturedUrl()).not.toContain("transaction_type");
  });

  it("date filters are appended", async () => {
    mockFetch(200, emptyBffExpenses);
    await getBffExpenses({ start: "2025-01-01", end: "2025-01-31" });
    const url = capturedUrl();
    expect(url).toContain("start=2025-01-01");
    expect(url).toContain("end=2025-01-31");
  });

  it("all filters combined", async () => {
    mockFetch(200, emptyBffExpenses);
    await getBffExpenses({ start: "2025-03-01", end: "2025-03-31", category_id: 2, transaction_type: "income", page: 2, page_size: 10 });
    const url = capturedUrl();
    expect(url).toContain("start=2025-03-01");
    expect(url).toContain("category_id=2");
    expect(url).toContain("transaction_type=income");
    expect(url).toContain("page=2");
  });
});

// ─── HTTP methods ─────────────────────────────────────────────────────────────

describe("HTTP methods", () => {
  it("createExpense sends POST", async () => {
    mockFetch(201, {});
    await createExpense({ amount: 100, date: "2025-03-01", entry_type: "texto", transaction_type: "outcome" });
    const [, options] = (fetch as ReturnType<typeof vi.fn>).mock.calls[0];
    expect(options.method).toBe("POST");
  });

  it("updateExpense sends PUT", async () => {
    mockFetch(200, {});
    await updateExpense("abc-123", {});
    const [, options] = (fetch as ReturnType<typeof vi.fn>).mock.calls[0];
    expect(options.method).toBe("PUT");
  });

  it("deleteExpense sends DELETE", async () => {
    mockFetch(204);
    await deleteExpense("abc-123");
    const [, options] = (fetch as ReturnType<typeof vi.fn>).mock.calls[0];
    expect(options.method).toBe("DELETE");
  });

  it("JWT is sent in Authorization header", async () => {
    mockFetch(200, emptyBffExpenses);
    await getBffExpenses();
    const [, options] = (fetch as ReturnType<typeof vi.fn>).mock.calls[0];
    expect(options.headers["Authorization"]).toBe("Bearer test-jwt");
  });
});
```

- [ ] **Step 3: Run frontend tests**

```bash
cd personal-finances-frontend
npm run test
```

Expected: all tests PASS. The removed functions are no longer tested; `getBffExpenses` tests pass.

- [ ] **Step 4: Commit**

```bash
git add src/lib/api.ts src/test/api.test.ts
git commit -m "feat: add getBffExpenses to api.ts; remove obsolete read functions"
```

---

## Task 7: Frontend — Dashboard Page

**Files:**
- Modify: `src/app/(protected)/dashboard/page.tsx`

- [ ] **Step 1: Replace the dashboard page**

Replace the full content of `src/app/(protected)/dashboard/page.tsx` with:

```tsx
import { createClient } from "@/lib/supabase/server";
import { SummaryCards } from "@/components/dashboard/SummaryCards";
import { CategoryPieChart } from "@/components/dashboard/CategoryPieChart";
import { BffDashboardResponse, SummaryItem } from "@/lib/api";

async function fetchDashboard(
  jwt: string,
  start: string,
  end: string
): Promise<BffDashboardResponse> {
  const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;
  const empty: BffDashboardResponse = { outcome_summary: [], income_summary: [], transaction_count: 0 };
  try {
    const res = await fetch(
      `${baseUrl}/api/v2/bff/dashboard?start=${start}&end=${end}`,
      { headers: { Authorization: `Bearer ${jwt}` }, cache: "no-store" }
    );
    if (!res.ok) return empty;
    return res.json();
  } catch {
    return empty;
  }
}

export default async function DashboardPage() {
  const supabase = await createClient();
  const { data: { session } } = await supabase.auth.getSession();
  const jwt = session?.access_token ?? "";

  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const start = `${year}-${month}-01`;
  const lastDay = new Date(year, now.getMonth() + 1, 0).getDate();
  const end = `${year}-${month}-${String(lastDay).padStart(2, "0")}`;

  const monthLabel = now.toLocaleDateString("en-US", { month: "long", year: "numeric" });

  const { outcome_summary, income_summary, transaction_count } = await fetchDashboard(jwt, start, end);

  const totalOutcome = outcome_summary.reduce((sum, item) => sum + parseFloat(item.total), 0);
  const totalIncome = income_summary.reduce((sum, item) => sum + parseFloat(item.total), 0);

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold text-neutral-900 dark:text-dark-primary">Dashboard</h1>
        <p className="text-sm text-neutral-500 dark:text-dark-muted mt-1 capitalize">{monthLabel}</p>
      </div>

      <SummaryCards
        totalIncome={totalIncome}
        totalOutcome={totalOutcome}
        transactionCount={transaction_count}
      />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <CategoryPieChart data={outcome_summary} />

        <div className="bg-white dark:bg-dark-surface border border-neutral-200 dark:border-dark-border rounded-xl shadow p-6">
          <h3 className="text-base font-semibold text-neutral-900 dark:text-dark-primary mb-4">
            Top expenses this month
          </h3>
          {outcome_summary.length === 0 ? (
            <div className="flex items-center justify-center h-48 text-neutral-400 dark:text-dark-muted text-sm">
              No data available for this month
            </div>
          ) : (
            <ul className="flex flex-col gap-3">
              {outcome_summary
                .slice()
                .sort((a, b) => parseFloat(b.total) - parseFloat(a.total))
                .map((item: SummaryItem) => {
                  const pct = totalOutcome > 0 ? (parseFloat(item.total) / totalOutcome) * 100 : 0;
                  return (
                    <li key={item.category}>
                      <div className="flex justify-between text-sm mb-1">
                        <span className="text-neutral-700 dark:text-dark-secondary font-medium">
                          {item.category}
                        </span>
                        <span className="font-bold text-neutral-900 dark:text-dark-primary">
                          {parseFloat(item.total).toLocaleString("en-US", {
                            style: "currency",
                            currency: "BRL",
                          })}
                        </span>
                      </div>
                      <div className="h-2 bg-neutral-100 dark:bg-dark-surface2 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-brand-500 rounded-full transition-all"
                          style={{ width: `${pct.toFixed(1)}%` }}
                        />
                      </div>
                    </li>
                  );
                })}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Verify TypeScript compiles**

```bash
cd personal-finances-frontend
npm run build 2>&1 | head -30
```

Expected: no TypeScript errors on `dashboard/page.tsx`.

- [ ] **Step 3: Commit**

```bash
git add src/app/\(protected\)/dashboard/page.tsx
git commit -m "feat: dashboard page uses single BFF call"
```

---

## Task 8: Frontend — Expenses Page and ExpenseModal

**Files:**
- Modify: `src/components/expenses/ExpenseModal.tsx`
- Modify: `src/app/(protected)/expenses/page.tsx`
- Modify: `src/test/ExpenseModal.test.tsx`

- [ ] **Step 1: Update ExpenseModal — accept categories as prop**

Replace the full content of `src/components/expenses/ExpenseModal.tsx` with:

```tsx
"use client";

import { useEffect, useState } from "react";
import { Modal } from "@/components/ui/Modal";
import { Button } from "@/components/ui/Button";
import { Input, Select } from "@/components/ui/Input";
import { CategoryOut, Expense, ExpenseInput, createExpense, updateExpense } from "@/lib/api";
import { useToast } from "@/hooks/useToast";

interface ExpenseModalProps {
  open: boolean;
  onClose: () => void;
  expense?: Expense | null;
  categories: CategoryOut[];
  onSaved: () => void;
}

const TIPO_OPTIONS = [
  { value: "texto", label: "Text" },
  { value: "imagem", label: "Image" },
  { value: "pdf", label: "PDF" },
];

const TRANSACTION_TYPE_OPTIONS = [
  { value: "outcome", label: "Expense" },
  { value: "income", label: "Income" },
];

const DEFAULT_FORM: ExpenseInput = {
  amount: 0,
  date: new Date().toISOString().split("T")[0],
  establishment: "",
  description: "",
  category_id: undefined,
  entry_type: "texto",
  transaction_type: "outcome",
};

export function ExpenseModal({ open, onClose, expense, categories, onSaved }: ExpenseModalProps) {
  const { showToast } = useToast();
  const [form, setForm] = useState<ExpenseInput>(DEFAULT_FORM);
  const [errors, setErrors] = useState<Partial<Record<keyof ExpenseInput, string>>>({});
  const [saving, setSaving] = useState(false);

  const isEditing = Boolean(expense);

  useEffect(() => {
    if (open) {
      if (expense) {
        setForm({
          amount: parseFloat(expense.amount),
          date: expense.date,
          establishment: expense.establishment || "",
          description: expense.description || "",
          category_id: expense.category_id ?? undefined,
          entry_type: expense.entry_type,
          transaction_type: expense.transaction_type ?? "outcome",
        });
      } else {
        setForm(DEFAULT_FORM);
      }
      setErrors({});
    }
  }, [open, expense]);

  const update = (key: keyof ExpenseInput, value: string | number | undefined) => {
    setForm((prev) => ({ ...prev, [key]: value }));
    setErrors((prev) => ({ ...prev, [key]: undefined }));
  };

  const validate = (): boolean => {
    const errs: Partial<Record<keyof ExpenseInput, string>> = {};
    if (!form.amount || form.amount <= 0) errs.amount = "Enter an amount greater than zero";
    if (!form.date) errs.date = "Enter the date";
    if (!form.entry_type) errs.entry_type = "Select the type";
    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    setSaving(true);
    try {
      const payload: ExpenseInput = {
        ...form,
        establishment: form.establishment || undefined,
        description: form.description || undefined,
      };

      const typeLabel = payload.transaction_type === "income" ? "Income" : "Expense";
      if (isEditing && expense) {
        await updateExpense(expense.id, payload);
        showToast(`${typeLabel} updated successfully!`, "success");
      } else {
        await createExpense(payload);
        showToast(`${typeLabel} created successfully!`, "success");
      }
      onSaved();
      onClose();
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Error saving expense";
      showToast(msg, "error");
    } finally {
      setSaving(false);
    }
  };

  const modalTitle = isEditing
    ? form.transaction_type === "income" ? "Edit Income" : "Edit Expense"
    : form.transaction_type === "income" ? "New Income" : "New Expense";

  return (
    <Modal open={open} onClose={onClose} title={modalTitle} maxWidth="md">
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Input
            label="Amount (R$)"
            type="number"
            step="0.01"
            min="0.01"
            value={form.amount || ""}
            onChange={(e) => update("amount", parseFloat(e.target.value) || 0)}
            error={errors.amount}
            required
          />
          <Input
            label="Date"
            type="date"
            value={form.date}
            onChange={(e) => update("date", e.target.value)}
            error={errors.date}
            required
          />
        </div>

        <Input
          label="Establishment"
          type="text"
          value={form.establishment}
          onChange={(e) => update("establishment", e.target.value)}
          placeholder="E.g.: Grocery Store"
        />

        <Input
          label="Description"
          type="text"
          value={form.description}
          onChange={(e) => update("description", e.target.value)}
          placeholder="Optional description"
        />

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Select
            label="Type"
            value={form.transaction_type}
            onChange={(e) => update("transaction_type", e.target.value as "income" | "outcome")}
            required
          >
            {TRANSACTION_TYPE_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </Select>

          <Select
            label="Category"
            value={form.category_id ?? ""}
            onChange={(e) =>
              update("category_id", e.target.value ? Number(e.target.value) : undefined)
            }
          >
            <option value="">No category</option>
            {categories
              .filter((c) => c.is_active)
              .map((cat) => (
                <option key={cat.id} value={cat.id}>
                  {cat.name}
                </option>
              ))}
          </Select>
        </div>

        <Select
          label="Entry type"
          value={form.entry_type}
          onChange={(e) => update("entry_type", e.target.value)}
          error={errors.entry_type}
          required
        >
          {TIPO_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </Select>

        <div className="flex gap-3 pt-2 justify-end">
          <Button type="button" variant="secondary" onClick={onClose} disabled={saving}>
            Cancel
          </Button>
          <Button type="submit" variant="primary" loading={saving}>
            {isEditing ? "Save changes" : "Create expense"}
          </Button>
        </div>
      </form>
    </Modal>
  );
}
```

- [ ] **Step 2: Update expenses/page.tsx — use getBffExpenses, pass categories to modal**

Replace the full content of `src/app/(protected)/expenses/page.tsx` with:

```tsx
"use client";

import { useCallback, useEffect, useState } from "react";
import {
  Expense,
  CategoryOut,
  PaginatedExpenses,
  getBffExpenses,
  deleteExpense,
} from "@/lib/api";
import { ExpenseTable } from "@/components/expenses/ExpenseTable";
import { ExpenseFilters, FilterValues } from "@/components/expenses/ExpenseFilters";
import { ExpenseModal } from "@/components/expenses/ExpenseModal";
import { Button } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";
import { useToast } from "@/hooks/useToast";
import { Plus, Download } from "lucide-react";
import { exportCsv } from "@/lib/api";

const PAGE_SIZE = 20;

const defaultFilters = (): FilterValues => {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const lastDay = new Date(year, now.getMonth() + 1, 0).getDate();
  return {
    start: `${year}-${month}-01`,
    end: `${year}-${month}-${String(lastDay).padStart(2, "0")}`,
    category_id: "",
    transaction_type: "",
  };
};

export default function ExpensesPage() {
  const { showToast } = useToast();

  const [data, setData] = useState<PaginatedExpenses>({
    items: [],
    total: 0,
    page: 1,
    page_size: PAGE_SIZE,
  });
  const [categories, setCategories] = useState<CategoryOut[]>([]);
  const [filters, setFilters] = useState<FilterValues>(defaultFilters);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);

  const [modalOpen, setModalOpen] = useState(false);
  const [editingExpense, setEditingExpense] = useState<Expense | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<Expense | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [exporting, setExporting] = useState(false);

  const loadExpenses = useCallback(async () => {
    setLoading(true);
    try {
      const result = await getBffExpenses({
        start: filters.start || undefined,
        end: filters.end || undefined,
        category_id: filters.category_id ? Number(filters.category_id) : undefined,
        transaction_type: (filters.transaction_type as "income" | "outcome") || undefined,
        page,
        page_size: PAGE_SIZE,
      });
      setData(result.transactions);
      setCategories(result.categories);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Error loading expenses";
      showToast(msg, "error");
    } finally {
      setLoading(false);
    }
  }, [filters, page, showToast]);

  useEffect(() => {
    loadExpenses();
  }, [loadExpenses]);

  const handleFiltersChange = (newFilters: FilterValues) => {
    setFilters(newFilters);
    setPage(1);
  };

  const handleResetFilters = () => {
    setFilters(defaultFilters());
    setPage(1);
  };

  const handleEdit = (expense: Expense) => {
    setEditingExpense(expense);
    setModalOpen(true);
  };

  const handleNewExpense = () => {
    setEditingExpense(null);
    setModalOpen(true);
  };

  const handleModalClose = () => {
    setModalOpen(false);
    setEditingExpense(null);
  };

  const handleSaved = () => {
    setPage(1);
    loadExpenses();
  };

  const handleDeleteConfirm = async () => {
    if (!deleteTarget) return;
    setDeleting(true);
    try {
      await deleteExpense(deleteTarget.id);
      showToast("Expense deleted successfully", "success");
      setDeleteTarget(null);
      loadExpenses();
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Error deleting expense";
      showToast(msg, "error");
    } finally {
      setDeleting(false);
    }
  };

  const handleExport = async () => {
    setExporting(true);
    try {
      const blob = await exportCsv(filters.start, filters.end);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `despesas-${filters.start}-${filters.end}.csv`;
      a.click();
      URL.revokeObjectURL(url);
      showToast("CSV exported successfully!", "success");
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Error exporting CSV";
      showToast(msg, "error");
    } finally {
      setExporting(false);
    }
  };

  return (
    <>
      <div className="flex flex-col gap-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-neutral-900 dark:text-dark-primary">Expenses</h1>
            <p className="text-sm text-neutral-500 dark:text-dark-muted mt-1">
              Manage your expenses
            </p>
          </div>
          <div className="flex gap-2">
            <Button
              variant="secondary"
              onClick={handleExport}
              loading={exporting}
              title="Export CSV"
            >
              <Download size={16} />
              <span className="hidden sm:inline">Export CSV</span>
            </Button>
            <Button variant="primary" onClick={handleNewExpense} aria-label="New expense">
              <Plus size={16} />
              <span className="hidden sm:inline" aria-hidden="true">New expense</span>
            </Button>
          </div>
        </div>

        <ExpenseFilters
          filters={filters}
          categories={categories}
          onChange={handleFiltersChange}
          onReset={handleResetFilters}
        />

        <ExpenseTable
          expenses={data.items}
          total={data.total}
          page={page}
          pageSize={PAGE_SIZE}
          onPageChange={setPage}
          onEdit={handleEdit}
          onDelete={setDeleteTarget}
          loading={loading}
        />
      </div>

      <ExpenseModal
        open={modalOpen}
        onClose={handleModalClose}
        expense={editingExpense}
        categories={categories}
        onSaved={handleSaved}
      />

      <Modal
        open={Boolean(deleteTarget)}
        onClose={() => setDeleteTarget(null)}
        title="Delete Expense"
        maxWidth="sm"
      >
        <div className="flex flex-col gap-6">
          <p className="text-sm text-neutral-600 dark:text-dark-secondary">
            Are you sure you want to delete this expense?
          </p>
          {deleteTarget && (
            <div className="rounded-lg bg-danger-bg dark:bg-danger-bg-dark border border-danger/20 dark:border-danger-dark/20 px-4 py-3">
              <p className="text-sm font-medium text-danger dark:text-danger-dark">
                {deleteTarget.establishment || deleteTarget.description || "No description"} —{" "}
                {parseFloat(deleteTarget.amount).toLocaleString("en-US", {
                  style: "currency",
                  currency: "BRL",
                })}
              </p>
            </div>
          )}
          <div className="flex gap-3 justify-end">
            <Button variant="secondary" onClick={() => setDeleteTarget(null)} disabled={deleting}>
              Cancel
            </Button>
            <Button variant="danger" onClick={handleDeleteConfirm} loading={deleting}>
              Delete
            </Button>
          </div>
        </div>
      </Modal>
    </>
  );
}
```

- [ ] **Step 3: Update ExpenseModal.test.tsx — remove getCategories mock, pass categories as prop**

Replace the full content of `src/test/ExpenseModal.test.tsx` with:

```tsx
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { ExpenseModal } from "@/components/expenses/ExpenseModal";
import { CategoryOut, Expense } from "@/lib/api";

vi.mock("@/lib/api", () => ({
  createExpense: vi.fn().mockResolvedValue({}),
  updateExpense: vi.fn().mockResolvedValue({}),
}));

vi.mock("@/hooks/useToast", () => ({
  useToast: () => ({ showToast: vi.fn() }),
}));

vi.mock("@/components/ui/Modal", () => ({
  Modal: ({
    open,
    children,
    title,
  }: {
    open: boolean;
    children: React.ReactNode;
    title: string;
    onClose: () => void;
    maxWidth?: string;
  }) =>
    open ? (
      <div role="dialog" aria-label={title}>
        <h2>{title}</h2>
        {children}
      </div>
    ) : null,
}));

vi.mock("@/components/ui/Button", () => ({
  Button: ({
    children,
    onClick,
    type,
    disabled,
    loading,
  }: React.PropsWithChildren<{
    onClick?: () => void;
    type?: "button" | "submit" | "reset";
    disabled?: boolean;
    loading?: boolean;
    variant?: string;
  }>) => (
    <button type={type} onClick={onClick} disabled={disabled || loading}>
      {children}
    </button>
  ),
}));

vi.mock("@/components/ui/Input", () => ({
  Input: ({
    label,
    error,
    ...props
  }: { label: string; error?: string } & React.InputHTMLAttributes<HTMLInputElement>) => (
    <div>
      <label htmlFor={props.id ?? label}>{label}</label>
      <input id={props.id ?? label} {...props} />
      {error && <span role="alert">{error}</span>}
    </div>
  ),
  Select: ({
    label,
    children,
    ...props
  }: { label: string } & React.SelectHTMLAttributes<HTMLSelectElement>) => (
    <div>
      <label htmlFor={props.id ?? label}>{label}</label>
      <select id={props.id ?? label} {...props}>
        {children}
      </select>
    </div>
  ),
}));

const DEFAULT_CATEGORIES: CategoryOut[] = [
  { id: 1, name: "Alimentação", is_active: true },
  { id: 2, name: "Transporte", is_active: true },
];

function renderModal(
  open = true,
  expense: Expense | null = null,
  onSaved = vi.fn(),
  onClose = vi.fn(),
  categories = DEFAULT_CATEGORIES
) {
  return render(
    <ExpenseModal
      open={open}
      onClose={onClose}
      expense={expense}
      categories={categories}
      onSaved={onSaved}
    />
  );
}

const MOCK_EXPENSE: Expense = {
  id: "abc-123",
  amount: "150.00",
  date: "2025-03-10",
  establishment: "Mercado",
  description: "Compras",
  category: "Alimentação",
  category_id: 1,
  tax_id: null,
  entry_type: "texto",
  transaction_type: "outcome",
  confidence: 1.0,
  created_at: "2025-03-10T10:00:00",
};

describe("ExpenseModal — transaction_type field", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the Type select", () => {
    renderModal();
    expect(screen.getByLabelText("Type")).toBeInTheDocument();
  });

  it("Type select has Expense option", () => {
    renderModal();
    expect(screen.getByRole("option", { name: "Expense" })).toBeInTheDocument();
  });

  it("Type select has Income option", () => {
    renderModal();
    expect(screen.getByRole("option", { name: "Income" })).toBeInTheDocument();
  });

  it("defaults to Expense (outcome) on new transaction", () => {
    renderModal();
    const select = screen.getByLabelText("Type") as HTMLSelectElement;
    expect(select.value).toBe("outcome");
  });

  it("pre-fills transaction_type from existing expense", () => {
    const incomeExpense = { ...MOCK_EXPENSE, transaction_type: "income" as const };
    renderModal(true, incomeExpense);
    const select = screen.getByLabelText("Type") as HTMLSelectElement;
    expect(select.value).toBe("income");
  });

  it("title shows 'New Income' when transaction_type is income", () => {
    renderModal();
    fireEvent.change(screen.getByLabelText("Type"), { target: { value: "income" } });
    expect(screen.getByRole("dialog")).toHaveAttribute("aria-label", "New Income");
  });

  it("title shows 'New Expense' when transaction_type is outcome", () => {
    renderModal();
    expect(screen.getByRole("dialog")).toHaveAttribute("aria-label", "New Expense");
  });

  it("title shows 'Edit Income' when editing an income", () => {
    const incomeExpense = { ...MOCK_EXPENSE, transaction_type: "income" as const };
    renderModal(true, incomeExpense);
    expect(screen.getByRole("dialog")).toHaveAttribute("aria-label", "Edit Income");
  });

  it("title shows 'Edit Expense' when editing an outcome", () => {
    renderModal(true, MOCK_EXPENSE);
    expect(screen.getByRole("dialog")).toHaveAttribute("aria-label", "Edit Expense");
  });
});

describe("ExpenseModal — createExpense payload", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("sends transaction_type in the payload", async () => {
    const { createExpense } = await import("@/lib/api");
    renderModal();

    fireEvent.change(screen.getByLabelText("Amount (R$)"), { target: { value: "50" } });
    fireEvent.change(screen.getByLabelText("Type"), { target: { value: "income" } });
    fireEvent.submit(screen.getByRole("dialog").querySelector("form")!);

    await waitFor(() => {
      expect(createExpense).toHaveBeenCalledWith(
        expect.objectContaining({ transaction_type: "income" })
      );
    });
  });
});
```

- [ ] **Step 4: Run frontend tests**

```bash
cd personal-finances-frontend
npm run test
```

Expected: all tests PASS. The `ExpenseModal` tests no longer rely on async category loading.

- [ ] **Step 5: Verify TypeScript build**

```bash
npm run build 2>&1 | head -30
```

Expected: no TypeScript errors.

- [ ] **Step 6: Commit**

```bash
git add src/components/expenses/ExpenseModal.tsx \
        src/app/\(protected\)/expenses/page.tsx \
        src/test/ExpenseModal.test.tsx
git commit -m "feat: expenses page and modal use BFF endpoint; categories passed as prop"
```
