# Hexagonal Architecture — Phase 2: Domain Use Cases

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement all single-action use cases in `src/v2/domain/use_cases/`. Each use case receives only ports in `__init__` and exposes a single `execute()` method. All tests are pure unit tests — no Supabase, no HTTP, no LLM calls.

**Architecture:** Use cases are the application layer. They orchestrate ports to implement business rules. Stubs implement the ports in-memory for testing. The architectural contract (`domain-no-adapters`) keeps all use cases free of infrastructure imports.

**Tech Stack:** Python 3.12, Pydantic v2, pytest, pytest-asyncio

**Prerequisite:** Phase 1 complete. `pytest tests/v2/test_architecture.py` passes.

**Spec:** `docs/superpowers/specs/2026-04-11-hexagonal-architecture-design.md`

---

## File Map

**Create:**
- `src/v2/domain/use_cases/expenses/create_expense.py`
- `src/v2/domain/use_cases/expenses/list_expenses.py`
- `src/v2/domain/use_cases/expenses/get_expense.py`
- `src/v2/domain/use_cases/expenses/update_expense.py`
- `src/v2/domain/use_cases/expenses/delete_expense.py`
- `src/v2/domain/use_cases/expenses/__init__.py`
- `src/v2/domain/use_cases/categories/list_categories.py`
- `src/v2/domain/use_cases/categories/create_category.py`
- `src/v2/domain/use_cases/categories/update_category.py`
- `src/v2/domain/use_cases/categories/deactivate_category.py`
- `src/v2/domain/use_cases/categories/__init__.py`
- `src/v2/domain/use_cases/reports/get_summary.py`
- `src/v2/domain/use_cases/reports/get_monthly.py`
- `src/v2/domain/use_cases/reports/export_csv.py`
- `src/v2/domain/use_cases/reports/__init__.py`
- `src/v2/domain/use_cases/telegram/process_message.py`
- `src/v2/domain/use_cases/telegram/confirm_expense.py`
- `src/v2/domain/use_cases/telegram/cancel_expense.py`
- `src/v2/domain/use_cases/telegram/change_category.py`
- `src/v2/domain/use_cases/telegram/generate_telegram_report.py`
- `src/v2/domain/use_cases/telegram/__init__.py`
- `tests/v2/domain/__init__.py`
- `tests/v2/domain/test_expense_use_cases.py`
- `tests/v2/domain/test_category_use_cases.py`
- `tests/v2/domain/test_report_use_cases.py`
- `tests/v2/domain/test_telegram_use_cases.py`

---

## Shared test stubs

All test files in this phase use in-memory port stubs. Define them once per test file — do not share across files to keep each file self-contained.

The stubs below are the **canonical pattern** to copy into each test file.

```python
# ── Stub helpers used in every test file ────────────────────────────────────

import datetime as _dt
from decimal import Decimal
from uuid import UUID, uuid4

from src.v2.domain.entities.category import Category
from src.v2.domain.entities.expense import Expense, ExtractedExpense
from src.v2.domain.ports.category_repository import CategoryRepository, CategoryUpdate
from src.v2.domain.ports.expense_repository import (
    ExpenseFilters,
    ExpenseRepository,
    ExpenseUpdate,
)
from src.v2.domain.ports.llm_port import LLMPort
from src.v2.domain.ports.notifier_port import NotificationButton, NotifierPort
from src.v2.domain.ports.pending_state_port import PendingExpense, PendingStatePort


def _make_expense(expense_id: UUID | None = None) -> Expense:
    return Expense(
        id=expense_id or uuid4(),
        amount=Decimal("50.00"),
        date=_dt.date(2026, 1, 15),
        establishment="Test Store",
        description="Test purchase",
        category_id=1,
        category="Alimentação",
        tax_id=None,
        entry_type="text",
        transaction_type="outcome",
        confidence=0.9,
        created_at=_dt.datetime(2026, 1, 15, 10, 0, 0),
    )


def _make_extracted() -> ExtractedExpense:
    return ExtractedExpense(
        amount=Decimal("50.00"),
        date=_dt.date(2026, 1, 15),
        establishment="Test Store",
        entry_type="text",
        transaction_type="outcome",
        confidence=0.9,
    )


class StubExpenseRepository(ExpenseRepository):
    def __init__(self, expenses: list[Expense] | None = None):
        self._expenses: list[Expense] = list(expenses or [])

    async def save(self, expense: ExtractedExpense, category_id: int) -> Expense:
        saved = _make_expense()
        self._expenses.append(saved)
        return saved

    async def get_by_id(self, expense_id: UUID) -> Expense | None:
        return next((e for e in self._expenses if e.id == expense_id), None)

    async def list_paginated(
        self, filters: ExpenseFilters
    ) -> tuple[list[Expense], int]:
        return self._expenses, len(self._expenses)

    async def list_by_period(self, start, end, transaction_type=None) -> list[Expense]:
        return self._expenses

    async def get_recent(self, limit: int = 3) -> list[Expense]:
        return self._expenses[:limit]

    async def update(self, expense_id: UUID, data: ExpenseUpdate) -> Expense | None:
        return next((e for e in self._expenses if e.id == expense_id), None)

    async def delete(self, expense_id: UUID) -> bool:
        before = len(self._expenses)
        self._expenses = [e for e in self._expenses if e.id != expense_id]
        return len(self._expenses) < before


class StubCategoryRepository(CategoryRepository):
    def __init__(self, categories: list[Category] | None = None):
        self._categories: list[Category] = list(
            categories
            or [
                Category(id=1, name="Alimentação", is_active=True),
                Category(id=2, name="Transporte", is_active=True),
            ]
        )

    async def list_active(self) -> list[str]:
        return [c.name for c in self._categories if c.is_active]

    async def list_all(self) -> list[Category]:
        return self._categories

    async def create(self, name: str) -> Category:
        new_id = max((c.id for c in self._categories), default=0) + 1
        cat = Category(id=new_id, name=name, is_active=True)
        self._categories.append(cat)
        return cat

    async def update(self, category_id: int, data: CategoryUpdate) -> Category | None:
        for cat in self._categories:
            if cat.id == category_id:
                return Category(
                    id=cat.id,
                    name=data.name if data.name is not None else cat.name,
                    is_active=data.is_active if data.is_active is not None else cat.is_active,
                )
        return None

    async def deactivate(self, category_id: int) -> bool:
        for cat in self._categories:
            if cat.id == category_id:
                cat.is_active = False
                return True
        return False


class StubLLMPort(LLMPort):
    def __init__(
        self,
        extracted: ExtractedExpense | None = None,
        category: str = "Alimentação",
        duplicate_reason: str | None = None,
        report_text: str = "Report insight.",
    ):
        self._extracted = extracted or _make_extracted()
        self._category = category
        self._duplicate_reason = duplicate_reason
        self._report_text = report_text

    async def extract_from_image(self, image_b64: str) -> ExtractedExpense:
        return self._extracted

    async def extract_from_text(self, text: str) -> ExtractedExpense:
        return self._extracted

    async def categorize(self, expense: ExtractedExpense, categories: list[str]) -> str:
        return self._category

    async def check_duplicate(self, expense: ExtractedExpense, recent) -> str | None:
        return self._duplicate_reason

    async def generate_report(self, expenses, period: str) -> str:
        return self._report_text


class StubNotifierPort(NotifierPort):
    def __init__(self):
        self.sent_messages: list[dict] = []
        self.sent_files: list[dict] = []
        self.answered_callbacks: list[dict] = []
        self.edited_messages: list[dict] = []

    async def send_message(self, chat_id, text, parse_mode=None, buttons=None):
        self.sent_messages.append(
            {"chat_id": chat_id, "text": text, "parse_mode": parse_mode, "buttons": buttons}
        )

    async def send_file(self, chat_id, content, filename, caption):
        self.sent_files.append(
            {"chat_id": chat_id, "filename": filename, "caption": caption}
        )

    async def answer_callback(self, callback_id, text=None):
        self.answered_callbacks.append({"callback_id": callback_id, "text": text})

    async def edit_message(self, chat_id, message_id, text, parse_mode=None, buttons=None):
        self.edited_messages.append(
            {"chat_id": chat_id, "message_id": message_id, "text": text}
        )


class StubPendingStatePort(PendingStatePort):
    def __init__(self):
        self._store: dict[int, PendingExpense] = {}

    def set(self, chat_id: int, state: PendingExpense) -> None:
        self._store[chat_id] = state

    def get(self, chat_id: int) -> PendingExpense | None:
        state = self._store.get(chat_id)
        if state and state.is_expired():
            self.clear(chat_id)
            return None
        return state

    def update_category(self, chat_id: int, category: str, category_id: int) -> bool:
        state = self.get(chat_id)
        if state is None:
            return False
        state.category = category
        state.category_id = category_id
        return True

    def clear(self, chat_id: int) -> None:
        self._store.pop(chat_id, None)
```

---

## Task 6: Expense CRUD use cases

**Files:**
- Create: `src/v2/domain/use_cases/expenses/create_expense.py`
- Create: `src/v2/domain/use_cases/expenses/list_expenses.py`
- Create: `src/v2/domain/use_cases/expenses/get_expense.py`
- Create: `src/v2/domain/use_cases/expenses/update_expense.py`
- Create: `src/v2/domain/use_cases/expenses/delete_expense.py`
- Create: `src/v2/domain/use_cases/expenses/__init__.py` (empty)
- Create: `tests/v2/domain/__init__.py` (empty)
- Create: `tests/v2/domain/test_expense_use_cases.py`

- [ ] **Step 1: Create `tests/v2/domain/__init__.py`** (empty)

- [ ] **Step 2: Write `tests/v2/domain/test_expense_use_cases.py`**

```python
import datetime as _dt
from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from src.v2.domain.entities.category import Category
from src.v2.domain.entities.expense import Expense, ExtractedExpense
from src.v2.domain.exceptions import ExpenseNotFoundError
from src.v2.domain.ports.category_repository import CategoryRepository, CategoryUpdate
from src.v2.domain.ports.expense_repository import (
    ExpenseFilters,
    ExpenseRepository,
    ExpenseUpdate,
)
from src.v2.domain.use_cases.expenses.create_expense import (
    CreateExpense,
    CreateExpenseCommand,
)
from src.v2.domain.use_cases.expenses.delete_expense import (
    DeleteExpense,
    DeleteExpenseCommand,
)
from src.v2.domain.use_cases.expenses.get_expense import GetExpense, GetExpenseQuery
from src.v2.domain.use_cases.expenses.list_expenses import (
    ListExpenses,
    ListExpensesQuery,
)
from src.v2.domain.use_cases.expenses.update_expense import (
    UpdateExpense,
    UpdateExpenseCommand,
)


# ── Stubs ────────────────────────────────────────────────────────────────────

def _make_expense(expense_id: UUID | None = None) -> Expense:
    return Expense(
        id=expense_id or uuid4(),
        amount=Decimal("50.00"),
        date=_dt.date(2026, 1, 15),
        establishment="Test Store",
        description=None,
        category_id=1,
        category="Alimentação",
        tax_id=None,
        entry_type="text",
        transaction_type="outcome",
        confidence=0.9,
        created_at=_dt.datetime(2026, 1, 15, 10, 0),
    )


class StubExpenseRepository(ExpenseRepository):
    def __init__(self, expenses: list[Expense] | None = None):
        self._expenses: list[Expense] = list(expenses or [])

    async def save(self, expense: ExtractedExpense, category_id: int) -> Expense:
        saved = _make_expense()
        self._expenses.append(saved)
        return saved

    async def get_by_id(self, expense_id: UUID) -> Expense | None:
        return next((e for e in self._expenses if e.id == expense_id), None)

    async def list_paginated(self, filters: ExpenseFilters) -> tuple[list[Expense], int]:
        return self._expenses, len(self._expenses)

    async def list_by_period(self, start, end, transaction_type=None) -> list[Expense]:
        return self._expenses

    async def get_recent(self, limit: int = 3) -> list[Expense]:
        return self._expenses[:limit]

    async def update(self, expense_id: UUID, data: ExpenseUpdate) -> Expense | None:
        return next((e for e in self._expenses if e.id == expense_id), None)

    async def delete(self, expense_id: UUID) -> bool:
        before = len(self._expenses)
        self._expenses = [e for e in self._expenses if e.id != expense_id]
        return len(self._expenses) < before


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_expense_returns_saved_expense():
    repo = StubExpenseRepository()
    use_case = CreateExpense(repo)
    cmd = CreateExpenseCommand(
        amount=Decimal("50.00"),
        date=_dt.date(2026, 1, 15),
        category_id=1,
        entry_type="text",
        transaction_type="outcome",
        establishment="Test Store",
    )
    result = await use_case.execute(cmd)
    assert result.amount == Decimal("50.00")
    assert result.entry_type == "text"


@pytest.mark.asyncio
async def test_get_expense_returns_expense_when_found():
    expense = _make_expense()
    repo = StubExpenseRepository([expense])
    result = await GetExpense(repo).execute(GetExpenseQuery(expense_id=expense.id))
    assert result.id == expense.id


@pytest.mark.asyncio
async def test_get_expense_raises_when_not_found():
    repo = StubExpenseRepository()
    with pytest.raises(ExpenseNotFoundError):
        await GetExpense(repo).execute(GetExpenseQuery(expense_id=uuid4()))


@pytest.mark.asyncio
async def test_list_expenses_returns_paginated_results():
    expenses = [_make_expense() for _ in range(3)]
    repo = StubExpenseRepository(expenses)
    items, total = await ListExpenses(repo).execute(ListExpensesQuery())
    assert total == 3
    assert len(items) == 3


@pytest.mark.asyncio
async def test_list_expenses_caps_page_size_at_100():
    repo = StubExpenseRepository()
    query = ListExpensesQuery(page_size=999)
    # Should not raise; page_size is clamped inside the use case
    await ListExpenses(repo).execute(query)


@pytest.mark.asyncio
async def test_update_expense_returns_updated_expense():
    expense = _make_expense()
    repo = StubExpenseRepository([expense])
    result = await UpdateExpense(repo).execute(
        UpdateExpenseCommand(expense_id=expense.id, description="Updated")
    )
    assert result is not None


@pytest.mark.asyncio
async def test_update_expense_raises_when_not_found():
    repo = StubExpenseRepository()
    with pytest.raises(ExpenseNotFoundError):
        await UpdateExpense(repo).execute(
            UpdateExpenseCommand(expense_id=uuid4(), description="x")
        )


@pytest.mark.asyncio
async def test_delete_expense_succeeds_when_exists():
    expense = _make_expense()
    repo = StubExpenseRepository([expense])
    # Should not raise
    await DeleteExpense(repo).execute(DeleteExpenseCommand(expense_id=expense.id))


@pytest.mark.asyncio
async def test_delete_expense_raises_when_not_found():
    repo = StubExpenseRepository()
    with pytest.raises(ExpenseNotFoundError):
        await DeleteExpense(repo).execute(DeleteExpenseCommand(expense_id=uuid4()))
```

- [ ] **Step 3: Run tests — expect FAIL (use cases don't exist yet)**

```bash
pytest tests/v2/domain/test_expense_use_cases.py -v
```

Expected: `ModuleNotFoundError` or `ImportError`

- [ ] **Step 4: Create `src/v2/domain/use_cases/expenses/create_expense.py`**

```python
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Literal

from src.v2.domain.entities.expense import Expense, ExtractedExpense
from src.v2.domain.ports.expense_repository import ExpenseRepository


@dataclass
class CreateExpenseCommand:
    amount: Decimal
    date: date
    category_id: int
    entry_type: Literal["image", "text", "pdf"]
    transaction_type: Literal["income", "outcome"]
    establishment: str | None = None
    description: str | None = None
    tax_id: str | None = None


class CreateExpense:
    def __init__(self, repo: ExpenseRepository) -> None:
        self._repo = repo

    async def execute(self, cmd: CreateExpenseCommand) -> Expense:
        extracted = ExtractedExpense(
            amount=cmd.amount,
            date=cmd.date,
            establishment=cmd.establishment,
            description=cmd.description,
            tax_id=cmd.tax_id,
            entry_type=cmd.entry_type,
            transaction_type=cmd.transaction_type,
            confidence=1.0,
        )
        return await self._repo.save(extracted, cmd.category_id)
```

- [ ] **Step 5: Create `src/v2/domain/use_cases/expenses/get_expense.py`**

```python
from dataclasses import dataclass
from uuid import UUID

from src.v2.domain.entities.expense import Expense
from src.v2.domain.exceptions import ExpenseNotFoundError
from src.v2.domain.ports.expense_repository import ExpenseRepository


@dataclass
class GetExpenseQuery:
    expense_id: UUID


class GetExpense:
    def __init__(self, repo: ExpenseRepository) -> None:
        self._repo = repo

    async def execute(self, query: GetExpenseQuery) -> Expense:
        expense = await self._repo.get_by_id(query.expense_id)
        if expense is None:
            raise ExpenseNotFoundError(f"Expense {query.expense_id} not found")
        return expense
```

- [ ] **Step 6: Create `src/v2/domain/use_cases/expenses/list_expenses.py`**

```python
from dataclasses import dataclass, field
from datetime import date
from typing import Literal

from src.v2.domain.entities.expense import Expense
from src.v2.domain.ports.expense_repository import ExpenseFilters, ExpenseRepository


@dataclass
class ListExpensesQuery:
    start: date | None = None
    end: date | None = None
    category_id: int | None = None
    transaction_type: Literal["income", "outcome"] | None = None
    page: int = 1
    page_size: int = 20


class ListExpenses:
    def __init__(self, repo: ExpenseRepository) -> None:
        self._repo = repo

    async def execute(self, query: ListExpensesQuery) -> tuple[list[Expense], int]:
        filters = ExpenseFilters(
            start=query.start,
            end=query.end,
            category_id=query.category_id,
            transaction_type=query.transaction_type,
            page=query.page,
            page_size=min(query.page_size, 100),
        )
        return await self._repo.list_paginated(filters)
```

- [ ] **Step 7: Create `src/v2/domain/use_cases/expenses/update_expense.py`**

```python
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Literal
from uuid import UUID

from src.v2.domain.entities.expense import Expense
from src.v2.domain.exceptions import ExpenseNotFoundError
from src.v2.domain.ports.expense_repository import ExpenseRepository, ExpenseUpdate


@dataclass
class UpdateExpenseCommand:
    expense_id: UUID
    amount: Decimal | None = None
    date: date | None = None
    establishment: str | None = None
    description: str | None = None
    category_id: int | None = None
    tax_id: str | None = None
    entry_type: str | None = None
    transaction_type: Literal["income", "outcome"] | None = None


class UpdateExpense:
    def __init__(self, repo: ExpenseRepository) -> None:
        self._repo = repo

    async def execute(self, cmd: UpdateExpenseCommand) -> Expense:
        data = ExpenseUpdate(
            amount=str(cmd.amount) if cmd.amount is not None else None,
            date=cmd.date,
            establishment=cmd.establishment,
            description=cmd.description,
            category_id=cmd.category_id,
            tax_id=cmd.tax_id,
            entry_type=cmd.entry_type,
            transaction_type=cmd.transaction_type,
        )
        expense = await self._repo.update(cmd.expense_id, data)
        if expense is None:
            raise ExpenseNotFoundError(f"Expense {cmd.expense_id} not found")
        return expense
```

- [ ] **Step 8: Create `src/v2/domain/use_cases/expenses/delete_expense.py`**

```python
from dataclasses import dataclass
from uuid import UUID

from src.v2.domain.exceptions import ExpenseNotFoundError
from src.v2.domain.ports.expense_repository import ExpenseRepository


@dataclass
class DeleteExpenseCommand:
    expense_id: UUID


class DeleteExpense:
    def __init__(self, repo: ExpenseRepository) -> None:
        self._repo = repo

    async def execute(self, cmd: DeleteExpenseCommand) -> None:
        deleted = await self._repo.delete(cmd.expense_id)
        if not deleted:
            raise ExpenseNotFoundError(f"Expense {cmd.expense_id} not found")
```

- [ ] **Step 9: Create `src/v2/domain/use_cases/expenses/__init__.py`** (empty)

- [ ] **Step 10: Run tests — expect PASS**

```bash
pytest tests/v2/domain/test_expense_use_cases.py -v
```

Expected: `9 passed`

- [ ] **Step 11: Run arch test — still passes**

```bash
pytest tests/v2/test_architecture.py -v
```

Expected: `PASSED`

- [ ] **Step 12: Commit**

```bash
git add src/v2/domain/use_cases/expenses/ tests/v2/domain/
git commit -m "feat(v2): add expense CRUD use cases with unit tests"
```

---

## Task 7: Category CRUD use cases

**Files:**
- Create: `src/v2/domain/use_cases/categories/list_categories.py`
- Create: `src/v2/domain/use_cases/categories/create_category.py`
- Create: `src/v2/domain/use_cases/categories/update_category.py`
- Create: `src/v2/domain/use_cases/categories/deactivate_category.py`
- Create: `src/v2/domain/use_cases/categories/__init__.py` (empty)
- Create: `tests/v2/domain/test_category_use_cases.py`

- [ ] **Step 1: Write `tests/v2/domain/test_category_use_cases.py`**

```python
import pytest

from src.v2.domain.entities.category import Category
from src.v2.domain.exceptions import CategoryNotFoundError
from src.v2.domain.ports.category_repository import CategoryRepository, CategoryUpdate
from src.v2.domain.use_cases.categories.create_category import (
    CreateCategory,
    CreateCategoryCommand,
)
from src.v2.domain.use_cases.categories.deactivate_category import (
    DeactivateCategory,
    DeactivateCategoryCommand,
)
from src.v2.domain.use_cases.categories.list_categories import ListCategories
from src.v2.domain.use_cases.categories.update_category import (
    UpdateCategory,
    UpdateCategoryCommand,
)


class StubCategoryRepository(CategoryRepository):
    def __init__(self):
        self._categories: list[Category] = [
            Category(id=1, name="Alimentação", is_active=True),
            Category(id=2, name="Transporte", is_active=True),
        ]

    async def list_active(self) -> list[str]:
        return [c.name for c in self._categories if c.is_active]

    async def list_all(self) -> list[Category]:
        return self._categories

    async def create(self, name: str) -> Category:
        new_id = max(c.id for c in self._categories) + 1
        cat = Category(id=new_id, name=name, is_active=True)
        self._categories.append(cat)
        return cat

    async def update(self, category_id: int, data: CategoryUpdate) -> Category | None:
        for cat in self._categories:
            if cat.id == category_id:
                return Category(
                    id=cat.id,
                    name=data.name if data.name is not None else cat.name,
                    is_active=data.is_active if data.is_active is not None else cat.is_active,
                )
        return None

    async def deactivate(self, category_id: int) -> bool:
        for cat in self._categories:
            if cat.id == category_id:
                cat.is_active = False
                return True
        return False


@pytest.mark.asyncio
async def test_list_categories_returns_all():
    repo = StubCategoryRepository()
    result = await ListCategories(repo).execute()
    assert len(result) == 2
    assert result[0].name == "Alimentação"


@pytest.mark.asyncio
async def test_create_category_returns_new_category():
    repo = StubCategoryRepository()
    result = await CreateCategory(repo).execute(CreateCategoryCommand(name="Pets"))
    assert result.name == "Pets"
    assert result.is_active is True


@pytest.mark.asyncio
async def test_update_category_returns_updated():
    repo = StubCategoryRepository()
    result = await UpdateCategory(repo).execute(
        UpdateCategoryCommand(category_id=1, name="Comida")
    )
    assert result.name == "Comida"


@pytest.mark.asyncio
async def test_update_category_raises_when_not_found():
    repo = StubCategoryRepository()
    with pytest.raises(CategoryNotFoundError):
        await UpdateCategory(repo).execute(
            UpdateCategoryCommand(category_id=999, name="X")
        )


@pytest.mark.asyncio
async def test_deactivate_category_succeeds():
    repo = StubCategoryRepository()
    # Should not raise
    await DeactivateCategory(repo).execute(DeactivateCategoryCommand(category_id=1))


@pytest.mark.asyncio
async def test_deactivate_category_raises_when_not_found():
    repo = StubCategoryRepository()
    with pytest.raises(CategoryNotFoundError):
        await DeactivateCategory(repo).execute(DeactivateCategoryCommand(category_id=999))
```

- [ ] **Step 2: Run tests — expect FAIL**

```bash
pytest tests/v2/domain/test_category_use_cases.py -v
```

Expected: `ImportError`

- [ ] **Step 3: Create `src/v2/domain/use_cases/categories/list_categories.py`**

```python
from src.v2.domain.entities.category import Category
from src.v2.domain.ports.category_repository import CategoryRepository


class ListCategories:
    def __init__(self, repo: CategoryRepository) -> None:
        self._repo = repo

    async def execute(self) -> list[Category]:
        return await self._repo.list_all()
```

- [ ] **Step 4: Create `src/v2/domain/use_cases/categories/create_category.py`**

```python
from dataclasses import dataclass

from src.v2.domain.entities.category import Category
from src.v2.domain.ports.category_repository import CategoryRepository


@dataclass
class CreateCategoryCommand:
    name: str


class CreateCategory:
    def __init__(self, repo: CategoryRepository) -> None:
        self._repo = repo

    async def execute(self, cmd: CreateCategoryCommand) -> Category:
        return await self._repo.create(cmd.name)
```

- [ ] **Step 5: Create `src/v2/domain/use_cases/categories/update_category.py`**

```python
from dataclasses import dataclass

from src.v2.domain.entities.category import Category
from src.v2.domain.exceptions import CategoryNotFoundError
from src.v2.domain.ports.category_repository import CategoryRepository, CategoryUpdate


@dataclass
class UpdateCategoryCommand:
    category_id: int
    name: str | None = None
    is_active: bool | None = None


class UpdateCategory:
    def __init__(self, repo: CategoryRepository) -> None:
        self._repo = repo

    async def execute(self, cmd: UpdateCategoryCommand) -> Category:
        data = CategoryUpdate(name=cmd.name, is_active=cmd.is_active)
        category = await self._repo.update(cmd.category_id, data)
        if category is None:
            raise CategoryNotFoundError(f"Category {cmd.category_id} not found")
        return category
```

- [ ] **Step 6: Create `src/v2/domain/use_cases/categories/deactivate_category.py`**

```python
from dataclasses import dataclass

from src.v2.domain.exceptions import CategoryNotFoundError
from src.v2.domain.ports.category_repository import CategoryRepository


@dataclass
class DeactivateCategoryCommand:
    category_id: int


class DeactivateCategory:
    def __init__(self, repo: CategoryRepository) -> None:
        self._repo = repo

    async def execute(self, cmd: DeactivateCategoryCommand) -> None:
        deactivated = await self._repo.deactivate(cmd.category_id)
        if not deactivated:
            raise CategoryNotFoundError(f"Category {cmd.category_id} not found")
```

- [ ] **Step 7: Create `src/v2/domain/use_cases/categories/__init__.py`** (empty)

- [ ] **Step 8: Run tests — expect PASS**

```bash
pytest tests/v2/domain/test_category_use_cases.py -v
```

Expected: `6 passed`

- [ ] **Step 9: Commit**

```bash
git add src/v2/domain/use_cases/categories/ tests/v2/domain/test_category_use_cases.py
git commit -m "feat(v2): add category CRUD use cases with unit tests"
```

---

## Task 8: Report use cases

**Files:**
- Create: `src/v2/domain/use_cases/reports/get_summary.py`
- Create: `src/v2/domain/use_cases/reports/get_monthly.py`
- Create: `src/v2/domain/use_cases/reports/export_csv.py`
- Create: `src/v2/domain/use_cases/reports/__init__.py` (empty)
- Create: `tests/v2/domain/test_report_use_cases.py`

- [ ] **Step 1: Write `tests/v2/domain/test_report_use_cases.py`**

```python
import datetime as _dt
from decimal import Decimal
from uuid import uuid4

import pytest

from src.v2.domain.entities.expense import Expense, ExtractedExpense
from src.v2.domain.ports.expense_repository import (
    ExpenseFilters,
    ExpenseRepository,
    ExpenseUpdate,
)
from src.v2.domain.use_cases.reports.export_csv import ExportCsv, ExportCsvQuery
from src.v2.domain.use_cases.reports.get_monthly import GetMonthly, GetMonthlyQuery
from src.v2.domain.use_cases.reports.get_summary import GetSummary, GetSummaryQuery
from uuid import UUID


def _make_expense(category: str, amount: str, month: int) -> Expense:
    return Expense(
        id=uuid4(),
        amount=Decimal(amount),
        date=_dt.date(2026, month, 15),
        establishment="Store",
        description=None,
        category_id=1,
        category=category,
        tax_id=None,
        entry_type="text",
        transaction_type="outcome",
        confidence=0.9,
        created_at=_dt.datetime(2026, month, 15, 10, 0),
    )


class StubExpenseRepository(ExpenseRepository):
    def __init__(self, expenses: list[Expense]):
        self._expenses = expenses

    async def save(self, expense: ExtractedExpense, category_id: int) -> Expense:
        raise NotImplementedError

    async def get_by_id(self, expense_id: UUID) -> Expense | None:
        raise NotImplementedError

    async def list_paginated(self, filters: ExpenseFilters) -> tuple[list[Expense], int]:
        raise NotImplementedError

    async def list_by_period(self, start, end, transaction_type=None) -> list[Expense]:
        return self._expenses

    async def get_recent(self, limit: int = 3) -> list[Expense]:
        raise NotImplementedError

    async def update(self, expense_id: UUID, data: ExpenseUpdate) -> Expense | None:
        raise NotImplementedError

    async def delete(self, expense_id: UUID) -> bool:
        raise NotImplementedError


@pytest.mark.asyncio
async def test_get_summary_aggregates_by_category():
    expenses = [
        _make_expense("Alimentação", "30.00", 1),
        _make_expense("Alimentação", "20.00", 1),
        _make_expense("Transporte", "15.00", 1),
    ]
    repo = StubExpenseRepository(expenses)
    result = await GetSummary(repo).execute(
        GetSummaryQuery(start=_dt.date(2026, 1, 1), end=_dt.date(2026, 1, 31))
    )
    by_cat = {item.category: item.total for item in result}
    assert by_cat["Alimentação"] == Decimal("50.00")
    assert by_cat["Transporte"] == Decimal("15.00")


@pytest.mark.asyncio
async def test_get_summary_returns_empty_for_no_expenses():
    repo = StubExpenseRepository([])
    result = await GetSummary(repo).execute(
        GetSummaryQuery(start=_dt.date(2026, 1, 1), end=_dt.date(2026, 1, 31))
    )
    assert result == []


@pytest.mark.asyncio
async def test_get_monthly_groups_by_month():
    expenses = [
        _make_expense("Alimentação", "100.00", 1),
        _make_expense("Transporte", "50.00", 2),
    ]
    repo = StubExpenseRepository(expenses)
    result = await GetMonthly(repo).execute(GetMonthlyQuery(year=2026))
    months = {item.month: item for item in result}
    assert months[1].total == Decimal("100.00")
    assert months[2].total == Decimal("50.00")


@pytest.mark.asyncio
async def test_export_csv_returns_utf8_bom_bytes():
    expenses = [_make_expense("Alimentação", "45.90", 1)]
    repo = StubExpenseRepository(expenses)
    result = await ExportCsv(repo).execute(
        ExportCsvQuery(start=_dt.date(2026, 1, 1), end=_dt.date(2026, 1, 31))
    )
    assert isinstance(result, bytes)
    # UTF-8 BOM for Excel compatibility
    assert result.startswith(b"\xef\xbb\xbf")
    content = result.decode("utf-8-sig")
    assert "Alimentação" in content
    assert "45.90" in content


@pytest.mark.asyncio
async def test_export_csv_has_header_row():
    repo = StubExpenseRepository([])
    result = await ExportCsv(repo).execute(
        ExportCsvQuery(start=_dt.date(2026, 1, 1), end=_dt.date(2026, 1, 31))
    )
    content = result.decode("utf-8-sig")
    assert "date" in content
    assert "amount" in content
    assert "category" in content
```

- [ ] **Step 2: Run tests — expect FAIL**

```bash
pytest tests/v2/domain/test_report_use_cases.py -v
```

Expected: `ImportError`

- [ ] **Step 3: Create `src/v2/domain/use_cases/reports/get_summary.py`**

```python
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Literal

from src.v2.domain.ports.expense_repository import ExpenseRepository


@dataclass
class SummaryItem:
    category: str
    total: Decimal


@dataclass
class GetSummaryQuery:
    start: date
    end: date
    transaction_type: Literal["income", "outcome"] | None = None


class GetSummary:
    def __init__(self, repo: ExpenseRepository) -> None:
        self._repo = repo

    async def execute(self, query: GetSummaryQuery) -> list[SummaryItem]:
        expenses = await self._repo.list_by_period(
            query.start, query.end, query.transaction_type
        )
        totals: dict[str, Decimal] = {}
        for expense in expenses:
            totals[expense.category] = (
                totals.get(expense.category, Decimal("0")) + expense.amount
            )
        return [
            SummaryItem(category=cat, total=total)
            for cat, total in sorted(totals.items())
        ]
```

- [ ] **Step 4: Create `src/v2/domain/use_cases/reports/get_monthly.py`**

```python
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Literal

from src.v2.domain.ports.expense_repository import ExpenseRepository


@dataclass
class MonthlyByCategoryItem:
    category: str
    total: Decimal


@dataclass
class MonthlyItem:
    month: int
    total: Decimal
    by_category: list[MonthlyByCategoryItem]


@dataclass
class GetMonthlyQuery:
    year: int
    transaction_type: Literal["income", "outcome"] | None = None


class GetMonthly:
    def __init__(self, repo: ExpenseRepository) -> None:
        self._repo = repo

    async def execute(self, query: GetMonthlyQuery) -> list[MonthlyItem]:
        expenses = await self._repo.list_by_period(
            date(query.year, 1, 1),
            date(query.year, 12, 31),
            query.transaction_type,
        )
        by_month: dict[int, dict[str, Decimal]] = {}
        for expense in expenses:
            m = expense.date.month
            if m not in by_month:
                by_month[m] = {}
            by_month[m][expense.category] = (
                by_month[m].get(expense.category, Decimal("0")) + expense.amount
            )
        return [
            MonthlyItem(
                month=month,
                total=sum(cats.values(), Decimal("0")),
                by_category=[
                    MonthlyByCategoryItem(category=cat, total=total)
                    for cat, total in sorted(cats.items())
                ],
            )
            for month, cats in sorted(by_month.items())
        ]
```

- [ ] **Step 5: Create `src/v2/domain/use_cases/reports/export_csv.py`**

```python
import csv
import io
from dataclasses import dataclass
from datetime import date
from typing import Literal

from src.v2.domain.ports.expense_repository import ExpenseRepository


@dataclass
class ExportCsvQuery:
    start: date
    end: date
    transaction_type: Literal["income", "outcome"] | None = None


class ExportCsv:
    def __init__(self, repo: ExpenseRepository) -> None:
        self._repo = repo

    async def execute(self, query: ExportCsvQuery) -> bytes:
        expenses = await self._repo.list_by_period(
            query.start, query.end, query.transaction_type
        )
        output = io.StringIO()
        output.write("\ufeff")  # UTF-8 BOM for Excel compatibility
        writer = csv.writer(output)
        writer.writerow(
            ["date", "amount", "establishment", "category", "description",
             "tax_id", "entry_type", "transaction_type"]
        )
        for expense in expenses:
            writer.writerow([
                expense.date.isoformat(),
                str(expense.amount),
                expense.establishment or "",
                expense.category,
                expense.description or "",
                expense.tax_id or "",
                expense.entry_type,
                expense.transaction_type,
            ])
        return output.getvalue().encode("utf-8")
```

- [ ] **Step 6: Create `src/v2/domain/use_cases/reports/__init__.py`** (empty)

- [ ] **Step 7: Run tests — expect PASS**

```bash
pytest tests/v2/domain/test_report_use_cases.py -v
```

Expected: `5 passed`

- [ ] **Step 8: Commit**

```bash
git add src/v2/domain/use_cases/reports/ tests/v2/domain/test_report_use_cases.py
git commit -m "feat(v2): add report use cases (summary, monthly, CSV export)"
```

---

## Task 9: Telegram use cases

**Files:**
- Create: `src/v2/domain/use_cases/telegram/process_message.py`
- Create: `src/v2/domain/use_cases/telegram/confirm_expense.py`
- Create: `src/v2/domain/use_cases/telegram/cancel_expense.py`
- Create: `src/v2/domain/use_cases/telegram/change_category.py`
- Create: `src/v2/domain/use_cases/telegram/generate_telegram_report.py`
- Create: `src/v2/domain/use_cases/telegram/__init__.py` (empty)
- Create: `tests/v2/domain/test_telegram_use_cases.py`

- [ ] **Step 1: Write `tests/v2/domain/test_telegram_use_cases.py`**

```python
import datetime as _dt
from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from src.v2.domain.entities.category import Category
from src.v2.domain.entities.expense import Expense, ExtractedExpense
from src.v2.domain.ports.category_repository import CategoryRepository, CategoryUpdate
from src.v2.domain.ports.expense_repository import (
    ExpenseFilters,
    ExpenseRepository,
    ExpenseUpdate,
)
from src.v2.domain.ports.llm_port import LLMPort
from src.v2.domain.ports.notifier_port import NotificationButton, NotifierPort
from src.v2.domain.ports.pending_state_port import PendingExpense, PendingStatePort
from src.v2.domain.use_cases.telegram.cancel_expense import (
    CancelExpense,
    CancelExpenseCommand,
)
from src.v2.domain.use_cases.telegram.change_category import (
    ChangeCategory,
    ChangeCategoryCommand,
)
from src.v2.domain.use_cases.telegram.confirm_expense import (
    ConfirmExpense,
    ConfirmExpenseCommand,
)
from src.v2.domain.use_cases.telegram.generate_telegram_report import (
    GenerateTelegramReport,
    GenerateTelegramReportCommand,
)
from src.v2.domain.use_cases.telegram.process_message import (
    ProcessMessage,
    ProcessMessageCommand,
)


# ── Stubs ────────────────────────────────────────────────────────────────────

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


def _make_extracted() -> ExtractedExpense:
    return ExtractedExpense(
        amount=Decimal("50.00"),
        date=_dt.date(2026, 1, 15),
        establishment="Store",
        entry_type="text",
        transaction_type="outcome",
        confidence=0.9,
    )


class StubExpenseRepository(ExpenseRepository):
    def __init__(self):
        self._saved: list[Expense] = []

    async def save(self, expense: ExtractedExpense, category_id: int) -> Expense:
        e = _make_expense()
        self._saved.append(e)
        return e

    async def get_by_id(self, expense_id: UUID) -> Expense | None:
        return None

    async def list_paginated(self, filters) -> tuple[list[Expense], int]:
        return [], 0

    async def list_by_period(self, start, end, transaction_type=None) -> list[Expense]:
        return self._saved

    async def get_recent(self, limit: int = 3) -> list[Expense]:
        return []

    async def update(self, expense_id, data) -> Expense | None:
        return None

    async def delete(self, expense_id) -> bool:
        return False


class StubCategoryRepository(CategoryRepository):
    async def list_active(self) -> list[str]:
        return ["Alimentação", "Transporte"]

    async def list_all(self) -> list[Category]:
        return [
            Category(id=1, name="Alimentação", is_active=True),
            Category(id=2, name="Transporte", is_active=True),
        ]

    async def create(self, name: str) -> Category:
        return Category(id=3, name=name, is_active=True)

    async def update(self, category_id, data) -> Category | None:
        return None

    async def deactivate(self, category_id) -> bool:
        return False


class StubLLMPort(LLMPort):
    def __init__(self, duplicate_reason: str | None = None):
        self._duplicate_reason = duplicate_reason

    async def extract_from_image(self, image_b64: str) -> ExtractedExpense:
        return _make_extracted()

    async def extract_from_text(self, text: str) -> ExtractedExpense:
        return _make_extracted()

    async def categorize(self, expense, categories) -> str:
        return "Alimentação"

    async def check_duplicate(self, expense, recent) -> str | None:
        return self._duplicate_reason

    async def generate_report(self, expenses, period: str) -> str:
        return "Gastos dentro do normal."


class StubNotifierPort(NotifierPort):
    def __init__(self):
        self.sent_messages: list[dict] = []
        self.edited_messages: list[dict] = []
        self.sent_files: list[dict] = []

    async def send_message(self, chat_id, text, parse_mode=None, buttons=None):
        self.sent_messages.append({"chat_id": chat_id, "text": text, "buttons": buttons})

    async def send_file(self, chat_id, content, filename, caption):
        self.sent_files.append({"chat_id": chat_id, "filename": filename})

    async def answer_callback(self, callback_id, text=None):
        pass

    async def edit_message(self, chat_id, message_id, text, parse_mode=None, buttons=None):
        self.edited_messages.append({"chat_id": chat_id, "text": text})


class StubPendingStatePort(PendingStatePort):
    def __init__(self, initial: PendingExpense | None = None, chat_id: int | None = None):
        self._store: dict[int, PendingExpense] = {}
        if initial and chat_id:
            self._store[chat_id] = initial

    def set(self, chat_id, state):
        self._store[chat_id] = state

    def get(self, chat_id) -> PendingExpense | None:
        s = self._store.get(chat_id)
        if s and s.is_expired():
            self.clear(chat_id)
            return None
        return s

    def update_category(self, chat_id, category, category_id) -> bool:
        s = self.get(chat_id)
        if s is None:
            return False
        s.category = category
        s.category_id = category_id
        return True

    def clear(self, chat_id):
        self._store.pop(chat_id, None)


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_process_message_sends_confirmation_for_text():
    notifier = StubNotifierPort()
    pending = StubPendingStatePort()
    use_case = ProcessMessage(
        llm=StubLLMPort(),
        category_repo=StubCategoryRepository(),
        pending=pending,
        notifier=notifier,
    )
    await use_case.execute(
        ProcessMessageCommand(chat_id=123, entry_type="text", text="gastei 50 no mercado")
    )
    assert len(notifier.sent_messages) == 1
    msg = notifier.sent_messages[0]
    assert msg["chat_id"] == 123
    assert msg["buttons"] is not None  # confirmation keyboard was sent
    assert pending.get(123) is not None  # state stored


@pytest.mark.asyncio
async def test_process_message_sends_confirmation_for_image():
    notifier = StubNotifierPort()
    pending = StubPendingStatePort()
    use_case = ProcessMessage(
        llm=StubLLMPort(),
        category_repo=StubCategoryRepository(),
        pending=pending,
        notifier=notifier,
    )
    await use_case.execute(
        ProcessMessageCommand(chat_id=123, entry_type="image", image_b64="base64data")
    )
    assert len(notifier.sent_messages) == 1
    assert pending.get(123) is not None


@pytest.mark.asyncio
async def test_confirm_expense_saves_and_notifies():
    extracted = _make_extracted()
    state = PendingExpense(
        extracted=extracted,
        category="Alimentação",
        category_id=1,
        chat_id=123,
        message_id=42,
    )
    repo = StubExpenseRepository()
    notifier = StubNotifierPort()
    pending = StubPendingStatePort(initial=state, chat_id=123)
    use_case = ConfirmExpense(
        repo=repo,
        llm=StubLLMPort(duplicate_reason=None),
        pending=pending,
        notifier=notifier,
    )
    await use_case.execute(ConfirmExpenseCommand(chat_id=123, message_id=42))
    assert len(repo._saved) == 1
    assert pending.get(123) is None  # cleared after save
    assert any("registrada" in m["text"] for m in notifier.sent_messages)


@pytest.mark.asyncio
async def test_confirm_expense_warns_on_duplicate():
    extracted = _make_extracted()
    state = PendingExpense(
        extracted=extracted,
        category="Alimentação",
        category_id=1,
        chat_id=123,
        message_id=42,
    )
    repo = StubExpenseRepository()
    notifier = StubNotifierPort()
    pending = StubPendingStatePort(initial=state, chat_id=123)
    use_case = ConfirmExpense(
        repo=repo,
        llm=StubLLMPort(duplicate_reason="Same store, same amount, yesterday"),
        pending=pending,
        notifier=notifier,
    )
    await use_case.execute(ConfirmExpenseCommand(chat_id=123, message_id=42))
    assert len(repo._saved) == 0  # not saved yet
    assert pending.get(123) is not None  # still pending
    assert any("duplicidade" in m["text"].lower() or "duplicate" in m["text"].lower()
               for m in notifier.sent_messages + notifier.edited_messages)


@pytest.mark.asyncio
async def test_confirm_expense_force_skips_duplicate_check():
    extracted = _make_extracted()
    state = PendingExpense(
        extracted=extracted,
        category="Alimentação",
        category_id=1,
        chat_id=123,
        message_id=42,
    )
    repo = StubExpenseRepository()
    notifier = StubNotifierPort()
    pending = StubPendingStatePort(initial=state, chat_id=123)
    use_case = ConfirmExpense(
        repo=repo,
        llm=StubLLMPort(duplicate_reason="would be a duplicate"),
        pending=pending,
        notifier=notifier,
    )
    await use_case.execute(
        ConfirmExpenseCommand(chat_id=123, message_id=42, skip_duplicate_check=True)
    )
    assert len(repo._saved) == 1


@pytest.mark.asyncio
async def test_cancel_expense_clears_pending_and_notifies():
    state = PendingExpense(
        extracted=_make_extracted(),
        category="Alimentação",
        category_id=1,
        chat_id=123,
        message_id=42,
    )
    notifier = StubNotifierPort()
    pending = StubPendingStatePort(initial=state, chat_id=123)
    use_case = CancelExpense(pending=pending, notifier=notifier)
    await use_case.execute(CancelExpenseCommand(chat_id=123, message_id=42))
    assert pending.get(123) is None
    assert len(notifier.edited_messages) == 1


@pytest.mark.asyncio
async def test_change_category_updates_pending_and_resends_confirmation():
    state = PendingExpense(
        extracted=_make_extracted(),
        category="Alimentação",
        category_id=1,
        chat_id=123,
        message_id=42,
    )
    notifier = StubNotifierPort()
    pending = StubPendingStatePort(initial=state, chat_id=123)
    use_case = ChangeCategory(pending=pending, notifier=notifier)
    await use_case.execute(
        ChangeCategoryCommand(
            chat_id=123,
            message_id=42,
            new_category="Transporte",
            new_category_id=2,
        )
    )
    updated = pending.get(123)
    assert updated is not None
    assert updated.category == "Transporte"
    assert len(notifier.edited_messages) == 1


@pytest.mark.asyncio
async def test_generate_telegram_report_sends_message():
    notifier = StubNotifierPort()
    repo = StubExpenseRepository()
    use_case = GenerateTelegramReport(repo=repo, llm=StubLLMPort(), notifier=notifier)
    await use_case.execute(
        GenerateTelegramReportCommand(
            chat_id=123,
            period_label="Janeiro 2026",
            start=_dt.date(2026, 1, 1),
            end=_dt.date(2026, 1, 31),
        )
    )
    assert len(notifier.sent_messages) == 1
    assert "123" not in notifier.sent_messages[0]["text"]  # shouldn't leak chat_id
```

- [ ] **Step 2: Run tests — expect FAIL**

```bash
pytest tests/v2/domain/test_telegram_use_cases.py -v
```

Expected: `ImportError`

- [ ] **Step 3: Create `src/v2/domain/use_cases/telegram/process_message.py`**

```python
from dataclasses import dataclass
from typing import Literal

from src.v2.domain.entities.category import Category
from src.v2.domain.ports.category_repository import CategoryRepository
from src.v2.domain.ports.llm_port import LLMPort
from src.v2.domain.ports.notifier_port import NotificationButton, NotifierPort
from src.v2.domain.ports.pending_state_port import PendingExpense, PendingStatePort


@dataclass
class ProcessMessageCommand:
    chat_id: int
    entry_type: Literal["image", "text", "pdf"]
    image_b64: str | None = None
    text: str | None = None
    message_id: int | None = None


class ProcessMessage:
    def __init__(
        self,
        llm: LLMPort,
        category_repo: CategoryRepository,
        pending: PendingStatePort,
        notifier: NotifierPort,
    ) -> None:
        self._llm = llm
        self._category_repo = category_repo
        self._pending = pending
        self._notifier = notifier

    async def execute(self, cmd: ProcessMessageCommand) -> None:
        # 1. Extract
        if cmd.entry_type == "image" and cmd.image_b64:
            extracted = await self._llm.extract_from_image(cmd.image_b64)
        elif cmd.text:
            extracted = await self._llm.extract_from_text(cmd.text)
        else:
            await self._notifier.send_message(
                cmd.chat_id, "Não consegui processar a mensagem. Tente novamente."
            )
            return

        # 2. Fetch categories + categorize
        categories = await self._category_repo.list_all()
        category_names = [c.name for c in categories]
        category_name = await self._llm.categorize(extracted, category_names)
        category_id = next(
            (c.id for c in categories if c.name == category_name),
            categories[0].id if categories else 1,
        )

        # 3. Store pending state
        state = PendingExpense(
            extracted=extracted,
            category=category_name,
            category_id=category_id,
            chat_id=cmd.chat_id,
            message_id=cmd.message_id,
        )
        self._pending.set(cmd.chat_id, state)

        # 4. Build and send confirmation message
        amount_str = f"R$ {extracted.amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        date_str = (
            extracted.date.strftime("%d/%m/%Y") if extracted.date else "data não encontrada"
        )
        lines = [
            f"*{extracted.establishment or 'Estabelecimento desconhecido'}*",
            f"Valor: {amount_str}",
            f"Data: {date_str}",
            f"Categoria: {category_name}",
        ]
        if extracted.description:
            lines.append(f"Descrição: {extracted.description}")

        buttons = [
            [
                NotificationButton(text="Confirmar ✅", callback_data="confirm"),
                NotificationButton(text="Cancelar ❌", callback_data="cancel"),
            ],
            [
                NotificationButton(text="Alterar Categoria 🏷️", callback_data="edit_category"),
            ],
        ]
        await self._notifier.send_message(
            cmd.chat_id,
            "\n".join(lines),
            parse_mode="Markdown",
            buttons=buttons,
        )
```

- [ ] **Step 4: Create `src/v2/domain/use_cases/telegram/confirm_expense.py`**

```python
from dataclasses import dataclass, field

from src.v2.domain.ports.expense_repository import ExpenseRepository
from src.v2.domain.ports.llm_port import LLMPort
from src.v2.domain.ports.notifier_port import NotificationButton, NotifierPort
from src.v2.domain.ports.pending_state_port import PendingStatePort


@dataclass
class ConfirmExpenseCommand:
    chat_id: int
    message_id: int
    skip_duplicate_check: bool = False


class ConfirmExpense:
    def __init__(
        self,
        repo: ExpenseRepository,
        llm: LLMPort,
        pending: PendingStatePort,
        notifier: NotifierPort,
    ) -> None:
        self._repo = repo
        self._llm = llm
        self._pending = pending
        self._notifier = notifier

    async def execute(self, cmd: ConfirmExpenseCommand) -> None:
        state = self._pending.get(cmd.chat_id)
        if state is None:
            await self._notifier.edit_message(
                cmd.chat_id, cmd.message_id,
                "⏱️ Operação expirada. Envie novamente."
            )
            return

        if not cmd.skip_duplicate_check:
            await self._notifier.edit_message(
                cmd.chat_id, cmd.message_id, "⏳ Verificando duplicidades..."
            )
            recent = await self._repo.get_recent(3)
            duplicate_reason = await self._llm.check_duplicate(state.extracted, recent)
            if duplicate_reason:
                buttons = [[
                    NotificationButton(
                        text="Salvar mesmo assim", callback_data="force_confirm"
                    ),
                    NotificationButton(text="Cancelar ❌", callback_data="cancel"),
                ]]
                await self._notifier.edit_message(
                    cmd.chat_id,
                    cmd.message_id,
                    f"⚠️ *Possível duplicidade detectada*\n\n{duplicate_reason}\n\nDeseja salvar mesmo assim?",
                    parse_mode="Markdown",
                    buttons=buttons,
                )
                return

        # Save
        await self._notifier.edit_message(
            cmd.chat_id, cmd.message_id, "⏳ Gravando no banco de dados..."
        )
        try:
            expense = await self._repo.save(state.extracted, state.category_id)
            self._pending.clear(cmd.chat_id)
            amount_str = (
                f"R$ {expense.amount:,.2f}"
                .replace(",", "X").replace(".", ",").replace("X", ".")
            )
            await self._notifier.send_message(
                cmd.chat_id,
                f"✅ Despesa de *{amount_str}* em *{expense.category}* registrada com sucesso!",
                parse_mode="Markdown",
            )
        except Exception:
            await self._notifier.send_message(
                cmd.chat_id, "❌ Erro ao salvar a despesa. Tente novamente."
            )
```

- [ ] **Step 5: Create `src/v2/domain/use_cases/telegram/cancel_expense.py`**

```python
from dataclasses import dataclass

from src.v2.domain.ports.notifier_port import NotifierPort
from src.v2.domain.ports.pending_state_port import PendingStatePort


@dataclass
class CancelExpenseCommand:
    chat_id: int
    message_id: int


class CancelExpense:
    def __init__(self, pending: PendingStatePort, notifier: NotifierPort) -> None:
        self._pending = pending
        self._notifier = notifier

    async def execute(self, cmd: CancelExpenseCommand) -> None:
        self._pending.clear(cmd.chat_id)
        await self._notifier.edit_message(
            cmd.chat_id, cmd.message_id, "❌ Despesa cancelada."
        )
```

- [ ] **Step 6: Create `src/v2/domain/use_cases/telegram/change_category.py`**

```python
from dataclasses import dataclass

from src.v2.domain.ports.notifier_port import NotificationButton, NotifierPort
from src.v2.domain.ports.pending_state_port import PendingStatePort


@dataclass
class ChangeCategoryCommand:
    chat_id: int
    message_id: int
    new_category: str
    new_category_id: int


class ChangeCategory:
    def __init__(self, pending: PendingStatePort, notifier: NotifierPort) -> None:
        self._pending = pending
        self._notifier = notifier

    async def execute(self, cmd: ChangeCategoryCommand) -> None:
        updated = self._pending.update_category(
            cmd.chat_id, cmd.new_category, cmd.new_category_id
        )
        if not updated:
            await self._notifier.edit_message(
                cmd.chat_id, cmd.message_id,
                "⏱️ Operação expirada. Envie a despesa novamente."
            )
            return

        state = self._pending.get(cmd.chat_id)
        if state is None:
            return

        extracted = state.extracted
        amount_str = (
            f"R$ {extracted.amount:,.2f}"
            .replace(",", "X").replace(".", ",").replace("X", ".")
        )
        date_str = (
            extracted.date.strftime("%d/%m/%Y") if extracted.date else "data não encontrada"
        )
        lines = [
            f"*{extracted.establishment or 'Estabelecimento desconhecido'}*",
            f"Valor: {amount_str}",
            f"Data: {date_str}",
            f"Categoria: {cmd.new_category}",
        ]
        if extracted.description:
            lines.append(f"Descrição: {extracted.description}")

        buttons = [
            [
                NotificationButton(text="Confirmar ✅", callback_data="confirm"),
                NotificationButton(text="Cancelar ❌", callback_data="cancel"),
            ],
            [
                NotificationButton(
                    text="Alterar Categoria 🏷️", callback_data="edit_category"
                ),
            ],
        ]
        await self._notifier.edit_message(
            cmd.chat_id,
            cmd.message_id,
            "\n".join(lines),
            parse_mode="Markdown",
            buttons=buttons,
        )
```

- [ ] **Step 7: Create `src/v2/domain/use_cases/telegram/generate_telegram_report.py`**

```python
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from src.v2.domain.ports.expense_repository import ExpenseRepository
from src.v2.domain.ports.llm_port import LLMPort
from src.v2.domain.ports.notifier_port import NotifierPort


@dataclass
class GenerateTelegramReportCommand:
    chat_id: int
    period_label: str
    start: date
    end: date


class GenerateTelegramReport:
    def __init__(
        self,
        repo: ExpenseRepository,
        llm: LLMPort,
        notifier: NotifierPort,
    ) -> None:
        self._repo = repo
        self._llm = llm
        self._notifier = notifier

    async def execute(self, cmd: GenerateTelegramReportCommand) -> None:
        expenses = await self._repo.list_by_period(cmd.start, cmd.end)

        if not expenses:
            await self._notifier.send_message(
                cmd.chat_id,
                f"Nenhuma despesa encontrada para o período: {cmd.period_label}.",
            )
            return

        # Aggregate by category
        totals: dict[str, Decimal] = {}
        grand_total = Decimal("0")
        for expense in expenses:
            totals[expense.category] = (
                totals.get(expense.category, Decimal("0")) + expense.amount
            )
            grand_total += expense.amount

        # Generate LLM insight
        insight = await self._llm.generate_report(expenses, cmd.period_label)

        # Format report
        lines = [f"📊 *Relatório — {cmd.period_label}*", ""]
        for cat, total in sorted(totals.items(), key=lambda x: x[1], reverse=True):
            pct = (total / grand_total * 100) if grand_total else Decimal("0")
            total_str = (
                f"R$ {total:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            )
            lines.append(f"• {cat}: {total_str} ({pct:.0f}%)")

        grand_str = (
            f"R$ {grand_total:,.2f}"
            .replace(",", "X").replace(".", ",").replace("X", ".")
        )
        lines += ["", f"*Total: {grand_str}*", "", f"💡 {insight}"]

        await self._notifier.send_message(
            cmd.chat_id, "\n".join(lines), parse_mode="Markdown"
        )
```

- [ ] **Step 8: Create `src/v2/domain/use_cases/telegram/__init__.py`** (empty)

- [ ] **Step 9: Run tests — expect PASS**

```bash
pytest tests/v2/domain/test_telegram_use_cases.py -v
```

Expected: `8 passed`

- [ ] **Step 10: Run full Phase 2 suite + arch test**

```bash
pytest tests/v2/ -v
```

Expected: all tests pass, including `test_architecture.py`

- [ ] **Step 11: Commit**

```bash
git add src/v2/domain/use_cases/telegram/ tests/v2/domain/test_telegram_use_cases.py
git commit -m "feat(v2): add telegram use cases (process, confirm, cancel, change-category, report)"
```

---

## Phase 2 complete

```bash
pytest tests/v2/ -v
```

Expected: `~24 tests passed`, `0 failed`

All domain use cases are implemented and tested in isolation. No Supabase, no HTTP, no LLM calls in any test. The architectural boundaries are enforced.

**Next:** Phase 3 — Secondary Adapters (`docs/superpowers/plans/2026-04-11-hexagonal-phase3-secondary-adapters.md`)
