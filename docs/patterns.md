# Backend — Code Patterns

## Pattern: Adding a new use case

Use cases live in `src/v2/domain/use_cases/<domain>/`. They receive dependencies via constructor injection and expose a single `execute()` method. They never import from adapters.

**1. Define a command dataclass (input) in the use case file:**

```python
# src/v2/domain/use_cases/expenses/create_expense.py
from dataclasses import dataclass
from decimal import Decimal
from datetime import date

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
```

**2. Inject the port (ABC interface) and implement `execute()`:**

```python
from src.v2.domain.ports.expense_repository import ExpenseRepository

class CreateExpense:
    def __init__(self, repo: ExpenseRepository) -> None:
        self._repo = repo

    async def execute(self, cmd: CreateExpenseCommand) -> Expense:
        extracted = ExtractedExpense(
            amount=cmd.amount,
            date=cmd.date,
            # ... map fields
        )
        return await self._repo.save(extracted, cmd.category_id)
```

**3. Define the port (if new) in `src/v2/domain/ports/`:**

```python
# src/v2/domain/ports/expense_repository.py
from abc import ABC, abstractmethod

class ExpenseRepository(ABC):
    @abstractmethod
    async def save(self, expense: ExtractedExpense, category_id: int) -> Expense: ...
```

**4. Implement the adapter in `src/v2/adapters/secondary/supabase/`:**

The adapter class inherits from the port and calls Supabase. It may import httpx, supabase-py, etc.

**5. Wire in `src/v2/bootstrap.py`:**

```python
repo = SupabaseExpenseRepository()
create_expense = CreateExpense(repo=repo)
container = UseCaseContainer(create_expense=create_expense, ...)
```

**6. Expose via a BFF router in `src/v2/adapters/primary/bff/routers/`:**

```python
@router.post("/transactions")
async def create_transaction(body: CreateTransactionRequest, deps = Depends(get_deps)):
    cmd = CreateExpenseCommand(amount=body.amount, ...)
    expense = await deps.create_expense.execute(cmd)
    return expense
```

---

## Pattern: Adding a new REST endpoint to an existing router

1. Add the Pydantic request/response model at the top of the router file.
2. Add the route function with `@router.get/post/put/delete(...)`.
3. Get the use case from `deps` (injected via `Depends(get_deps)`).
4. Call `await deps.<use_case>.execute(cmd)`.
5. Return the result directly (FastAPI serializes it).
