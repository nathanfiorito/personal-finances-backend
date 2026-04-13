# Hexagonal Architecture — Phase 1: Domain Foundation

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Scaffold the `src/v2/` package, define domain entities, all port ABCs, and wire up import-linter architectural tests — with zero infrastructure dependencies anywhere in `src/v2/domain/`.

**Architecture:** Hexagonal (Ports & Adapters). The domain layer is pure Python + Pydantic with no I/O. Ports are ABCs that secondary adapters will implement in Phase 3. Architectural contracts are enforced by `import-linter` running inside `pytest`.

**Tech Stack:** Python 3.12, Pydantic v2, import-linter, pytest, pytest-asyncio

**Spec:** `docs/superpowers/specs/2026-04-11-hexagonal-architecture-design.md`

---

## File Map

**Create:**
- `src/v2/__init__.py`
- `src/v2/domain/__init__.py`
- `src/v2/domain/entities/__init__.py`
- `src/v2/domain/entities/expense.py`
- `src/v2/domain/entities/category.py`
- `src/v2/domain/exceptions.py`
- `src/v2/domain/ports/__init__.py`
- `src/v2/domain/ports/expense_repository.py`
- `src/v2/domain/ports/category_repository.py`
- `src/v2/domain/ports/llm_port.py`
- `src/v2/domain/ports/notifier_port.py`
- `src/v2/domain/ports/pending_state_port.py`
- `src/v2/adapters/__init__.py`
- `src/v2/adapters/primary/__init__.py`
- `src/v2/adapters/secondary/__init__.py`
- `tests/v2/__init__.py`
- `tests/v2/conftest.py`
- `tests/v2/test_architecture.py`
- `.importlinter`

**Modify:**
- `requirements.txt` — add `import-linter`

---

## Task 1: Install import-linter and create the arch test (red)

**Files:**
- Modify: `requirements.txt`
- Create: `.importlinter`
- Create: `tests/v2/__init__.py`
- Create: `tests/v2/conftest.py`
- Create: `tests/v2/test_architecture.py`

- [ ] **Step 1: Add import-linter to requirements**

Open `requirements.txt` and add this line (keep alphabetical order with other packages):

```
import-linter==2.1
```

Install it:

```bash
pip install import-linter==2.1
```

- [ ] **Step 2: Create the `.importlinter` config** at the repo root (`personal-finances-backend/.importlinter`)

```ini
[importlinter]
root_packages =
    src

[importlinter:contract:domain-no-adapters]
name = Domain must not import from adapters
type = forbidden
source_modules =
    src.v2.domain
forbidden_modules =
    src.v2.adapters

[importlinter:contract:secondary-no-primary]
name = Secondary adapters must not import from primary adapters
type = forbidden
source_modules =
    src.v2.adapters.secondary
forbidden_modules =
    src.v2.adapters.primary

[importlinter:contract:entities-ports-purity]
name = Entities and ports must not import from use_cases
type = forbidden
source_modules =
    src.v2.domain.entities
    src.v2.domain.ports
forbidden_modules =
    src.v2.domain.use_cases
```

- [ ] **Step 3: Create `tests/v2/__init__.py`** (empty file)

```python
```

- [ ] **Step 4: Create `tests/v2/conftest.py`**

```python
import pytest


# Enable asyncio for all tests under tests/v2/ without needing
# @pytest.mark.asyncio on every function.
def pytest_configure(config):
    config.addinivalue_line(
        "markers", "asyncio: mark test as async"
    )
```

- [ ] **Step 5: Create `tests/v2/test_architecture.py`**

```python
import subprocess
import sys
from pathlib import Path


def test_hexagonal_contracts():
    """Enforce hexagonal architecture boundaries via import-linter.

    Runs `lint-imports` against the .importlinter config at the project root.
    Fails with a readable diff if any declared contract is violated.
    """
    project_root = Path(__file__).parent.parent.parent  # personal-finances-backend/
    result = subprocess.run(
        [sys.executable, "-m", "importlinter"],
        capture_output=True,
        text=True,
        cwd=str(project_root),
    )
    assert result.returncode == 0, (
        "Architecture contract violations detected:\n"
        + result.stdout
        + result.stderr
    )
```

- [ ] **Step 6: Run the test — expect it to PASS trivially** (no `src.v2` package yet, so no violations to detect)

```bash
cd personal-finances-backend
pytest tests/v2/test_architecture.py -v
```

Expected output:
```
PASSED tests/v2/test_architecture.py::test_hexagonal_contracts
```

- [ ] **Step 7: Commit**

```bash
git add requirements.txt .importlinter tests/v2/
git commit -m "feat(v2): add import-linter and architecture test scaffold"
```

---

## Task 2: Scaffold the `src/v2/` package skeleton

**Files:**
- Create: `src/v2/__init__.py`
- Create: `src/v2/domain/__init__.py`
- Create: `src/v2/domain/entities/__init__.py`
- Create: `src/v2/domain/ports/__init__.py`
- Create: `src/v2/domain/use_cases/__init__.py`
- Create: `src/v2/adapters/__init__.py`
- Create: `src/v2/adapters/primary/__init__.py`
- Create: `src/v2/adapters/primary/bff/__init__.py`
- Create: `src/v2/adapters/primary/bff/routers/__init__.py`
- Create: `src/v2/adapters/primary/telegram/__init__.py`
- Create: `src/v2/adapters/primary/telegram/handlers/__init__.py`
- Create: `src/v2/adapters/secondary/__init__.py`
- Create: `src/v2/adapters/secondary/supabase/__init__.py`
- Create: `src/v2/adapters/secondary/openrouter/__init__.py`
- Create: `src/v2/adapters/secondary/telegram_api/__init__.py`
- Create: `src/v2/adapters/secondary/memory/__init__.py`

- [ ] **Step 1: Create all `__init__.py` files** — every one is empty

```bash
mkdir -p src/v2/domain/entities \
         src/v2/domain/ports \
         src/v2/domain/use_cases \
         src/v2/adapters/primary/bff/routers \
         src/v2/adapters/primary/telegram/handlers \
         src/v2/adapters/secondary/supabase \
         src/v2/adapters/secondary/openrouter \
         src/v2/adapters/secondary/telegram_api \
         src/v2/adapters/secondary/memory

touch src/v2/__init__.py \
      src/v2/domain/__init__.py \
      src/v2/domain/entities/__init__.py \
      src/v2/domain/ports/__init__.py \
      src/v2/domain/use_cases/__init__.py \
      src/v2/adapters/__init__.py \
      src/v2/adapters/primary/__init__.py \
      src/v2/adapters/primary/bff/__init__.py \
      src/v2/adapters/primary/bff/routers/__init__.py \
      src/v2/adapters/primary/telegram/__init__.py \
      src/v2/adapters/primary/telegram/handlers/__init__.py \
      src/v2/adapters/secondary/__init__.py \
      src/v2/adapters/secondary/supabase/__init__.py \
      src/v2/adapters/secondary/openrouter/__init__.py \
      src/v2/adapters/secondary/telegram_api/__init__.py \
      src/v2/adapters/secondary/memory/__init__.py
```

- [ ] **Step 2: Run arch test again — still passes**

```bash
pytest tests/v2/test_architecture.py -v
```

Expected: `PASSED`

- [ ] **Step 3: Commit**

```bash
git add src/v2/
git commit -m "feat(v2): scaffold hexagonal package structure"
```

---

## Task 3: Domain entities

**Files:**
- Create: `src/v2/domain/entities/expense.py`
- Create: `src/v2/domain/entities/category.py`
- Create: `src/v2/domain/exceptions.py`

- [ ] **Step 1: Create `src/v2/domain/entities/expense.py`**

```python
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
```

- [ ] **Step 2: Create `src/v2/domain/entities/category.py`**

```python
from pydantic import BaseModel


class Category(BaseModel):
    id: int
    name: str
    is_active: bool
```

- [ ] **Step 3: Create `src/v2/domain/exceptions.py`**

```python
class DomainError(Exception):
    """Base class for all domain-level errors."""


class ExpenseNotFoundError(DomainError):
    pass


class CategoryNotFoundError(DomainError):
    pass


class DuplicateExpenseError(DomainError):
    pass


class CategoryAlreadyExistsError(DomainError):
    pass
```

- [ ] **Step 4: Run arch test — must still pass (entities import only pydantic/stdlib)**

```bash
pytest tests/v2/test_architecture.py -v
```

Expected: `PASSED`

- [ ] **Step 5: Commit**

```bash
git add src/v2/domain/entities/ src/v2/domain/exceptions.py
git commit -m "feat(v2): add domain entities and exceptions"
```

---

## Task 4: Domain ports

**Files:**
- Create: `src/v2/domain/ports/expense_repository.py`
- Create: `src/v2/domain/ports/category_repository.py`
- Create: `src/v2/domain/ports/llm_port.py`
- Create: `src/v2/domain/ports/notifier_port.py`
- Create: `src/v2/domain/ports/pending_state_port.py`

- [ ] **Step 1: Create `src/v2/domain/ports/expense_repository.py`**

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date
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
    amount: str | None = None          # string to avoid float precision issues
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
```

- [ ] **Step 2: Create `src/v2/domain/ports/category_repository.py`**

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass

from src.v2.domain.entities.category import Category


@dataclass
class CategoryUpdate:
    name: str | None = None
    is_active: bool | None = None


class CategoryRepository(ABC):
    @abstractmethod
    async def list_active(self) -> list[str]: ...

    @abstractmethod
    async def list_all(self) -> list[Category]: ...

    @abstractmethod
    async def create(self, name: str) -> Category: ...

    @abstractmethod
    async def update(
        self, category_id: int, data: CategoryUpdate
    ) -> Category | None: ...

    @abstractmethod
    async def deactivate(self, category_id: int) -> bool: ...
```

- [ ] **Step 3: Create `src/v2/domain/ports/llm_port.py`**

```python
from abc import ABC, abstractmethod

from src.v2.domain.entities.expense import Expense, ExtractedExpense


class LLMPort(ABC):
    @abstractmethod
    async def extract_from_image(self, image_b64: str) -> ExtractedExpense: ...

    @abstractmethod
    async def extract_from_text(self, text: str) -> ExtractedExpense: ...

    @abstractmethod
    async def categorize(
        self, expense: ExtractedExpense, categories: list[str]
    ) -> str: ...

    @abstractmethod
    async def check_duplicate(
        self, expense: ExtractedExpense, recent: list[Expense]
    ) -> str | None:
        """Return a human-readable reason string if duplicate, or None if not."""
        ...

    @abstractmethod
    async def generate_report(
        self, expenses: list[Expense], period: str
    ) -> str: ...
```

- [ ] **Step 4: Create `src/v2/domain/ports/notifier_port.py`**

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class NotificationButton:
    """A single inline button, adapter-agnostic."""

    text: str
    callback_data: str


class NotifierPort(ABC):
    @abstractmethod
    async def send_message(
        self,
        chat_id: int,
        text: str,
        parse_mode: str | None = None,
        buttons: list[list[NotificationButton]] | None = None,
    ) -> None: ...

    @abstractmethod
    async def send_file(
        self,
        chat_id: int,
        content: bytes,
        filename: str,
        caption: str,
    ) -> None: ...

    @abstractmethod
    async def answer_callback(
        self,
        callback_id: str,
        text: str | None = None,
    ) -> None: ...

    @abstractmethod
    async def edit_message(
        self,
        chat_id: int,
        message_id: int,
        text: str,
        parse_mode: str | None = None,
        buttons: list[list[NotificationButton]] | None = None,
    ) -> None: ...
```

- [ ] **Step 5: Create `src/v2/domain/ports/pending_state_port.py`**

```python
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from src.v2.domain.entities.expense import ExtractedExpense

_TTL_SECONDS = 600  # 10 minutes


@dataclass
class PendingExpense:
    extracted: ExtractedExpense
    category: str          # display name shown in confirmation message
    category_id: int       # used by ConfirmExpense to persist
    chat_id: int
    message_id: int | None = None
    expires_at: float = field(
        default_factory=lambda: time.monotonic() + _TTL_SECONDS
    )

    def is_expired(self) -> bool:
        return time.monotonic() > self.expires_at


class PendingStatePort(ABC):
    @abstractmethod
    def set(self, chat_id: int, state: PendingExpense) -> None: ...

    @abstractmethod
    def get(self, chat_id: int) -> PendingExpense | None: ...

    @abstractmethod
    def update_category(
        self, chat_id: int, category: str, category_id: int
    ) -> bool:
        """Update category on an existing pending state. Returns False if expired/missing."""
        ...

    @abstractmethod
    def clear(self, chat_id: int) -> None: ...
```

- [ ] **Step 6: Run arch test — must still pass (ports import only domain entities + stdlib/abc)**

```bash
pytest tests/v2/test_architecture.py -v
```

Expected: `PASSED`

- [ ] **Step 7: Commit**

```bash
git add src/v2/domain/ports/
git commit -m "feat(v2): add domain ports (ABC contracts for all secondary adapters)"
```

---

## Task 5: Verify arch test catches a real violation

This task proves the arch test is actually working, not just passing vacuously.

**Files:** (no permanent changes — we introduce and then revert a bad import)

- [ ] **Step 1: Temporarily add a bad import to `src/v2/domain/entities/expense.py`**

Add this line at the top of `src/v2/domain/entities/expense.py` (after the existing imports):

```python
from src.v2.adapters import secondary  # INTENTIONAL VIOLATION — will be removed
```

- [ ] **Step 2: Run the arch test — expect FAIL**

```bash
pytest tests/v2/test_architecture.py -v
```

Expected: `FAILED` with a message mentioning `entities-ports-purity` or `domain-no-adapters` contract.

- [ ] **Step 3: Remove the bad import** from `src/v2/domain/entities/expense.py`

Delete the line:

```python
from src.v2.adapters import secondary  # INTENTIONAL VIOLATION — will be removed
```

- [ ] **Step 4: Run arch test again — back to PASS**

```bash
pytest tests/v2/test_architecture.py -v
```

Expected: `PASSED`

- [ ] **Step 5: Commit (no code change — working tree is clean)**

```bash
git status  # should show nothing to commit
```

---

## Phase 1 complete

Run the full Phase 1 test suite to confirm everything is green:

```bash
pytest tests/v2/ -v
```

Expected:
```
PASSED tests/v2/test_architecture.py::test_hexagonal_contracts
1 passed in Xs
```

The domain layer (`src/v2/domain/`) is now fully defined with entities, ports, and exceptions. No infrastructure dependency exists anywhere inside it. The architectural test will catch any future violation automatically.

**Next:** Phase 2 — Domain Use Cases (`docs/superpowers/plans/2026-04-11-hexagonal-phase2-use-cases.md`)
