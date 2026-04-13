# Payment Method Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a required `payment_method` field (`"credit"` or `"debit"`) to expenses, persisted in the database and exposed in the BFF API and frontend create/edit modal and expense table.

**Architecture:** A `PaymentMethod` StrEnum lives in the domain entity. The BFF router accepts it as `Literal["credit", "debit"]`. The repository stores it as a plain VARCHAR column. The frontend adds a required Select field to the modal and a display column in the table.

**Tech Stack:** Python 3.12+, Pydantic v2, FastAPI, Supabase (PostgreSQL), pytest, Next.js 16, React 19, TypeScript, Vitest

---

## Files

| Action | Path |
|---|---|
| Modify | `personal-finances-backend/src/v2/domain/entities/expense.py` |
| Modify | `personal-finances-backend/src/v2/domain/ports/expense_repository.py` |
| Modify | `personal-finances-backend/src/v2/domain/use_cases/expenses/create_expense.py` |
| Modify | `personal-finances-backend/src/v2/domain/use_cases/expenses/update_expense.py` |
| Modify | `personal-finances-backend/src/v2/adapters/primary/bff/routers/transactions.py` |
| Modify | `personal-finances-backend/src/v2/adapters/secondary/supabase/expense_repository.py` |
| Modify | `personal-finances-backend/tests/v2/domain/test_expense_use_cases.py` |
| Modify | `personal-finances-backend/tests/v2/adapters/test_bff_transactions.py` |
| Modify | `personal-finances-frontend/src/lib/api.ts` |
| Modify | `personal-finances-frontend/src/components/expenses/ExpenseModal.tsx` |
| Modify | `personal-finances-frontend/src/components/expenses/ExpenseTable.tsx` |
| Modify | `personal-finances-frontend/src/test/ExpenseModal.test.tsx` |
| Modify | `personal-finances-frontend/src/test/ExpenseTable.test.tsx` |

---

### Task 1: Add PaymentMethod to domain entities and fix test fixtures

**Files:**
- Modify: `personal-finances-backend/src/v2/domain/entities/expense.py`
- Modify: `personal-finances-backend/tests/v2/domain/test_expense_use_cases.py`
- Modify: `personal-finances-backend/tests/v2/adapters/test_bff_transactions.py`

- [ ] **Step 1: Write failing test for PaymentMethod enum and Expense field**

Add to the top of `tests/v2/domain/test_expense_use_cases.py` (after the imports):

```python
def test_payment_method_enum_has_credit_and_debit():
    from src.v2.domain.entities.expense import PaymentMethod
    assert PaymentMethod.CREDIT == "credit"
    assert PaymentMethod.DEBIT == "debit"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd personal-finances-backend
pytest tests/v2/domain/test_expense_use_cases.py::test_payment_method_enum_has_credit_and_debit -v
```

Expected: `ImportError` or `FAILED` — `PaymentMethod` does not exist yet.

- [ ] **Step 3: Add PaymentMethod and update entity fields**

Replace the contents of `src/v2/domain/entities/expense.py` with:

```python
from datetime import date as _date
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class PaymentMethod(StrEnum):
    CREDIT = "credit"
    DEBIT = "debit"


class ExtractedExpense(BaseModel):
    """Expense data extracted from a receipt by the LLM. Not yet persisted."""

    amount: Decimal
    date: _date | None = None
    establishment: str | None = None
    description: str | None = None
    tax_id: str | None = None
    entry_type: Literal["image", "text", "pdf"]
    transaction_type: Literal["income", "outcome"] = "outcome"
    payment_method: PaymentMethod = PaymentMethod.DEBIT
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
    date: _date
    establishment: str | None
    description: str | None
    category_id: int
    category: str
    tax_id: str | None
    entry_type: str
    transaction_type: Literal["income", "outcome"]
    payment_method: PaymentMethod
    confidence: float | None
    created_at: datetime
```

- [ ] **Step 4: Update _make_expense() in both test files to include payment_method**

In `tests/v2/domain/test_expense_use_cases.py`, update `_make_expense()`:

```python
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
        payment_method="debit",
        confidence=0.9,
        created_at=_dt.datetime(2026, 1, 15, 10, 0),
    )
```

In `tests/v2/adapters/test_bff_transactions.py`, update `_make_expense()`:

```python
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
        payment_method="debit",
        confidence=0.9,
        created_at=_dt.datetime(2026, 1, 15, 10, 0),
    )
```

- [ ] **Step 5: Run all backend tests to verify they pass**

```bash
cd personal-finances-backend
pytest tests/ -v
```

Expected: all tests pass (including the new enum test).

- [ ] **Step 6: Commit**

```bash
cd personal-finances-backend
git add src/v2/domain/entities/expense.py tests/v2/domain/test_expense_use_cases.py tests/v2/adapters/test_bff_transactions.py
git commit -m "feat: add PaymentMethod enum and payment_method field to expense entities"
```

---

### Task 2: Update port, commands, and use cases

**Files:**
- Modify: `personal-finances-backend/src/v2/domain/ports/expense_repository.py`
- Modify: `personal-finances-backend/src/v2/domain/use_cases/expenses/create_expense.py`
- Modify: `personal-finances-backend/src/v2/domain/use_cases/expenses/update_expense.py`
- Test: `personal-finances-backend/tests/v2/domain/test_expense_use_cases.py`

- [ ] **Step 1: Write failing tests for updated commands**

Add to `tests/v2/domain/test_expense_use_cases.py`:

```python
@pytest.mark.asyncio
async def test_create_expense_command_accepts_payment_method():
    repo = StubExpenseRepository()
    cmd = CreateExpenseCommand(
        amount=Decimal("50.00"),
        date=_dt.date(2026, 1, 15),
        category_id=1,
        entry_type="manual",
        transaction_type="outcome",
        payment_method="credit",
    )
    result = await CreateExpense(repo).execute(cmd)
    assert result is not None


@pytest.mark.asyncio
async def test_update_expense_command_accepts_payment_method():
    expense = _make_expense()
    repo = StubExpenseRepository([expense])
    cmd = UpdateExpenseCommand(
        expense_id=expense.id,
        payment_method="credit",
    )
    result = await UpdateExpense(repo).execute(cmd)
    assert result is not None
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd personal-finances-backend
pytest tests/v2/domain/test_expense_use_cases.py::test_create_expense_command_accepts_payment_method tests/v2/domain/test_expense_use_cases.py::test_update_expense_command_accepts_payment_method -v
```

Expected: `FAILED` — `CreateExpenseCommand` does not accept `payment_method` yet.

- [ ] **Step 3: Update ExpenseUpdate in the port**

In `src/v2/domain/ports/expense_repository.py`, add `payment_method` to `ExpenseUpdate`:

```python
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
    payment_method: str | None = None
```

- [ ] **Step 4: Update CreateExpenseCommand and CreateExpense.execute()**

Replace the full content of `src/v2/domain/use_cases/expenses/create_expense.py`:

```python
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from src.v2.domain.entities.expense import Expense, ExtractedExpense
from src.v2.domain.ports.expense_repository import ExpenseRepository


@dataclass
class CreateExpenseCommand:
    amount: Decimal
    date: date
    category_id: int
    entry_type: str
    transaction_type: str
    payment_method: str
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
            payment_method=cmd.payment_method,
            confidence=1.0,
        )
        return await self._repo.save(extracted, cmd.category_id)
```

- [ ] **Step 5: Update UpdateExpenseCommand and UpdateExpense.execute()**

Replace the full content of `src/v2/domain/use_cases/expenses/update_expense.py`:

```python
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
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
    transaction_type: str | None = None
    payment_method: str | None = None


class UpdateExpense:
    def __init__(self, repo: ExpenseRepository) -> None:
        self._repo = repo

    async def execute(self, cmd: UpdateExpenseCommand) -> Expense:
        data = ExpenseUpdate(
            amount=cmd.amount,
            date=cmd.date,
            establishment=cmd.establishment,
            description=cmd.description,
            category_id=cmd.category_id,
            tax_id=cmd.tax_id,
            entry_type=cmd.entry_type,
            transaction_type=cmd.transaction_type,
            payment_method=cmd.payment_method,
        )
        expense = await self._repo.update(cmd.expense_id, data)
        if expense is None:
            raise ExpenseNotFoundError(f"Expense {cmd.expense_id} not found")
        return expense
```

- [ ] **Step 6: Run tests to verify they pass**

```bash
cd personal-finances-backend
pytest tests/v2/domain/test_expense_use_cases.py -v
```

Expected: all tests pass.

- [ ] **Step 7: Commit**

```bash
cd personal-finances-backend
git add src/v2/domain/ports/expense_repository.py src/v2/domain/use_cases/expenses/create_expense.py src/v2/domain/use_cases/expenses/update_expense.py tests/v2/domain/test_expense_use_cases.py
git commit -m "feat: add payment_method to expense commands and use cases"
```

---

### Task 3: Update BFF router

**Files:**
- Modify: `personal-finances-backend/src/v2/adapters/primary/bff/routers/transactions.py`
- Test: `personal-finances-backend/tests/v2/adapters/test_bff_transactions.py`

- [ ] **Step 1: Write failing tests**

Add to `tests/v2/adapters/test_bff_transactions.py`:

```python
def test_create_transaction_with_payment_method_returns_201():
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
            "entry_type": "manual",
            "transaction_type": "outcome",
            "payment_method": "credit",
        },
    )
    assert resp.status_code == 201


def test_create_transaction_without_payment_method_returns_422():
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
            "entry_type": "manual",
            "transaction_type": "outcome",
        },
    )
    assert resp.status_code == 422
```

Also update the existing `test_create_transaction_returns_201` to include `payment_method`:

```python
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
            "payment_method": "debit",
        },
    )
    assert resp.status_code == 201
```

- [ ] **Step 2: Run tests to verify new ones fail**

```bash
cd personal-finances-backend
pytest tests/v2/adapters/test_bff_transactions.py::test_create_transaction_with_payment_method_returns_201 tests/v2/adapters/test_bff_transactions.py::test_create_transaction_without_payment_method_returns_422 -v
```

Expected: `FAILED`.

- [ ] **Step 3: Update TransactionCreate and TransactionUpdate schemas and router handlers**

Replace the full content of `src/v2/adapters/primary/bff/routers/transactions.py`:

```python
from __future__ import annotations

from datetime import date as _date
from decimal import Decimal
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, status
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
    payment_method: Literal["credit", "debit"]
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
    payment_method: Literal["credit", "debit"] | None = None
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
            payment_method=body.payment_method,
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
                payment_method=body.payment_method,
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

- [ ] **Step 4: Run all backend tests**

```bash
cd personal-finances-backend
pytest tests/ -v
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
cd personal-finances-backend
git add src/v2/adapters/primary/bff/routers/transactions.py tests/v2/adapters/test_bff_transactions.py
git commit -m "feat: add payment_method to BFF transactions router"
```

---

### Task 4: Update Supabase repository and database schema

**Files:**
- Modify: `personal-finances-backend/src/v2/adapters/secondary/supabase/expense_repository.py`

- [ ] **Step 1: Add the database column**

Run this SQL in the Supabase SQL editor (or via migration):

```sql
ALTER TABLE transactions ADD COLUMN payment_method VARCHAR NOT NULL DEFAULT 'debit';
```

After running, remove the DEFAULT (makes it required for new rows without a default):

```sql
ALTER TABLE transactions ALTER COLUMN payment_method DROP DEFAULT;
```

- [ ] **Step 2: Update save() to include payment_method**

In `src/v2/adapters/secondary/supabase/expense_repository.py`, update the `save()` method's `record` dict:

```python
async def save(self, expense: ExtractedExpense, category_id: int) -> Expense:
    record = {
        "amount": str(expense.amount),
        "date": expense.date.isoformat() if expense.date else None,
        "establishment": expense.establishment,
        "description": expense.description,
        "category_id": category_id,
        "tax_id": expense.tax_id,
        "entry_type": expense.entry_type,
        "transaction_type": expense.transaction_type,
        "payment_method": str(expense.payment_method),
        "confidence": expense.confidence,
        "raw_data": {},
    }
    t = time.perf_counter()
    response = (
        await self._client.table(_TABLE)
        .insert(record)
        .execute()
    )
    logger.info("DB %s.insert %.0fms", _TABLE, (time.perf_counter() - t) * 1000)
    row_id = UUID(response.data[0]["id"])
    saved = await self.get_by_id(row_id)
    return saved  # type: ignore[return-value]
```

- [ ] **Step 3: Update update() to include payment_method**

In the same file, update the `update()` method's `payload` dict:

```python
async def update(self, expense_id: UUID, data: ExpenseUpdate) -> Expense | None:
    payload = {
        k: v
        for k, v in {
            "amount": str(data.amount) if data.amount is not None else None,
            "date": data.date.isoformat() if data.date else None,
            "establishment": data.establishment,
            "description": data.description,
            "category_id": data.category_id,
            "tax_id": data.tax_id,
            "entry_type": data.entry_type,
            "transaction_type": data.transaction_type,
            "payment_method": data.payment_method,
        }.items()
        if v is not None
    }
    if not payload:
        return await self.get_by_id(expense_id)
    t = time.perf_counter()
    await (
        self._client.table(_TABLE)
        .update(payload)
        .eq("id", str(expense_id))
        .execute()
    )
    logger.info(
        "DB %s.update %.0fms", _TABLE, (time.perf_counter() - t) * 1000
    )
    return await self.get_by_id(expense_id)
```

- [ ] **Step 4: Run backend tests**

```bash
cd personal-finances-backend
pytest tests/ -v
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
cd personal-finances-backend
git add src/v2/adapters/secondary/supabase/expense_repository.py
git commit -m "feat: persist payment_method in Supabase expense repository"
```

---

### Task 5: Frontend — update interfaces and modal

**Files:**
- Modify: `personal-finances-frontend/src/lib/api.ts`
- Modify: `personal-finances-frontend/src/components/expenses/ExpenseModal.tsx`
- Test: `personal-finances-frontend/src/test/ExpenseModal.test.tsx`

- [ ] **Step 1: Write failing tests for payment_method in modal**

Add to `src/test/ExpenseModal.test.tsx` (before the closing of the last `describe` block, or as a new describe):

First update `MOCK_EXPENSE` to include `payment_method`:

```typescript
const MOCK_EXPENSE: Expense = {
  id: "abc-123",
  amount: "150.00",
  date: "2025-03-10",
  establishment: "Mercado",
  description: "Compras",
  category: "Alimentação",
  category_id: 1,
  tax_id: null,
  entry_type: "text",
  transaction_type: "outcome",
  payment_method: "debit",
  confidence: 1.0,
  created_at: "2025-03-10T10:00:00",
};
```

Then add a new describe block:

```typescript
describe("ExpenseModal — payment_method field", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the Payment method select", () => {
    renderModal();
    expect(screen.getByLabelText("Payment method")).toBeInTheDocument();
  });

  it("defaults to debit on new transaction", () => {
    renderModal();
    const select = screen.getByLabelText("Payment method") as HTMLSelectElement;
    expect(select.value).toBe("debit");
  });

  it("pre-fills payment_method from existing expense", () => {
    const creditExpense = { ...MOCK_EXPENSE, payment_method: "credit" as const };
    renderModal(true, creditExpense);
    const select = screen.getByLabelText("Payment method") as HTMLSelectElement;
    expect(select.value).toBe("credit");
  });

  it("sends payment_method in the create payload", async () => {
    const { createExpense } = await import("@/lib/api");
    renderModal();
    fireEvent.change(screen.getByLabelText("Amount (R$)"), { target: { value: "50" } });
    fireEvent.change(screen.getByLabelText("Payment method"), { target: { value: "credit" } });
    fireEvent.submit(screen.getByRole("dialog").querySelector("form")!);
    await waitFor(() => {
      expect(createExpense).toHaveBeenCalledWith(
        expect.objectContaining({ payment_method: "credit" })
      );
    });
  });
});
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd personal-finances-frontend
npm run test -- --run ExpenseModal
```

Expected: `FAILED` — `payment_method` field not rendered yet.

- [ ] **Step 3: Add payment_method to api.ts interfaces**

In `src/lib/api.ts`, update `Expense`:

```typescript
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
  payment_method: "credit" | "debit";
  confidence: number | null;
  created_at: string;
}
```

Update `ExpenseInput`:

```typescript
export interface ExpenseInput {
  amount: number;
  date: string;
  establishment?: string;
  description?: string;
  category_id?: number;
  entry_type: string;
  transaction_type: "income" | "outcome";
  payment_method: "credit" | "debit";
}
```

- [ ] **Step 4: Update ExpenseModal.tsx**

Add `PAYMENT_METHOD_OPTIONS` constant (after `TRANSACTION_TYPE_OPTIONS`):

```typescript
const PAYMENT_METHOD_OPTIONS = [
  { value: "debit", label: "Debit" },
  { value: "credit", label: "Credit" },
];
```

Update `DEFAULT_FORM`:

```typescript
const DEFAULT_FORM: ExpenseInput = {
  amount: 0,
  date: new Date().toISOString().split("T")[0],
  establishment: "",
  description: "",
  category_id: undefined,
  entry_type: "manual",
  transaction_type: "outcome",
  payment_method: "debit",
};
```

Update the `useEffect` edit branch to include `payment_method`:

```typescript
setForm({
  amount: parseFloat(expense.amount),
  date: expense.date,
  establishment: expense.establishment || "",
  description: expense.description || "",
  category_id: expense.category_id ?? undefined,
  entry_type: expense.entry_type,
  transaction_type: expense.transaction_type ?? "outcome",
  payment_method: expense.payment_method ?? "debit",
});
```

In the JSX, replace the `<div className="grid grid-cols-1 sm:grid-cols-2 gap-4">` block that holds Type and Category with:

```tsx
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
    label="Payment method"
    value={form.payment_method}
    onChange={(e) => update("payment_method", e.target.value as "credit" | "debit")}
    required
  >
    {PAYMENT_METHOD_OPTIONS.map((opt) => (
      <option key={opt.value} value={opt.value}>
        {opt.label}
      </option>
    ))}
  </Select>
</div>

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
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
cd personal-finances-frontend
npm run test -- --run ExpenseModal
```

Expected: all tests pass.

- [ ] **Step 6: Commit**

```bash
cd personal-finances-frontend
git add src/lib/api.ts src/components/expenses/ExpenseModal.tsx src/test/ExpenseModal.test.tsx
git commit -m "feat: add payment_method field to expense modal and API interfaces"
```

---

### Task 6: Frontend — add Payment column to expense table

**Files:**
- Modify: `personal-finances-frontend/src/components/expenses/ExpenseTable.tsx`
- Test: `personal-finances-frontend/src/test/ExpenseTable.test.tsx`

- [ ] **Step 1: Read the current ExpenseTable test to understand fixtures**

```bash
cat personal-finances-frontend/src/test/ExpenseTable.test.tsx
```

- [ ] **Step 2: Write failing test for Payment column**

Find `MOCK_EXPENSES` (or the array of test expenses) in `src/test/ExpenseTable.test.tsx` and add `payment_method: "debit"` to each fixture object. Then add:

```typescript
it("renders a Payment column header", () => {
  // render the table with at least one expense
  expect(screen.getByText("Payment")).toBeInTheDocument();
});

it("displays Credit for credit payment method", () => {
  // render with an expense where payment_method is "credit"
  expect(screen.getByText("Credit")).toBeInTheDocument();
});
```

- [ ] **Step 3: Run tests to verify they fail**

```bash
cd personal-finances-frontend
npm run test -- --run ExpenseTable
```

Expected: `FAILED` — no "Payment" column yet.

- [ ] **Step 4: Add Payment column to desktop table header**

In `ExpenseTable.tsx`, update the `<thead>` row to add a Payment column after Type:

```tsx
<th className="px-4 py-3 text-center font-semibold text-neutral-600 dark:text-dark-secondary">Type</th>
<th className="px-4 py-3 text-center font-semibold text-neutral-600 dark:text-dark-secondary">Payment</th>
<th className="px-4 py-3 text-right font-semibold text-neutral-600 dark:text-dark-secondary">Actions</th>
```

Update the skeleton loader row (change the skeleton column count from 6 to 7):

```tsx
{Array.from({ length: 7 }).map((_, j) => (
```

Add the Payment cell to each data row (after the Type `<td>`):

```tsx
<td className="px-4 py-3 text-center">
  <TransactionTypeBadge type={expense.transaction_type ?? "outcome"} />
</td>
<td className="px-4 py-3 text-center text-sm text-neutral-600 dark:text-dark-secondary capitalize">
  {expense.payment_method === "credit" ? "Credit" : "Debit"}
</td>
```

- [ ] **Step 5: Run all frontend tests**

```bash
cd personal-finances-frontend
npm run test -- --run
```

Expected: all tests pass.

- [ ] **Step 6: Lint**

```bash
cd personal-finances-frontend
npm run lint
```

Expected: no errors.

- [ ] **Step 7: Commit**

```bash
cd personal-finances-frontend
git add src/components/expenses/ExpenseTable.tsx src/test/ExpenseTable.test.tsx
git commit -m "feat: add Payment column to expense table"
```
