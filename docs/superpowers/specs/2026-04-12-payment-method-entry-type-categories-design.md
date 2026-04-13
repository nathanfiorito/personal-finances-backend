# Design: Payment Method, Entry Type Removal, Categories Bug Fix

**Date:** 2026-04-12

## Overview

Three independent changes to the personal-finances app, to be implemented in parallel on separate branches:

1. **Payment Method field** — add Credit/Debit to expenses
2. **Entry Type removal** — hide the field from the frontend; auto-set to `"manual"` for REST-created entries
3. **Categories bug fix** — disabled categories not appearing on the Categories page; no way to re-enable them

---

## Feature 1: Payment Method

### Goal

Allow tracking whether an expense was paid by credit card or debit card.

### Database

New column on `transactions`:

```sql
ALTER TABLE transactions ADD COLUMN payment_method VARCHAR NOT NULL;
```

No migration strategy needed — database will be wiped before production use.

### Backend

**Domain entity (`src/v2/domain/entities/expense.py`):**

Add a `PaymentMethod` StrEnum:

```python
from enum import StrEnum

class PaymentMethod(StrEnum):
    CREDIT = "credit"
    DEBIT = "debit"
```

Add `payment_method: PaymentMethod` to `Expense` (required).

Add `payment_method: PaymentMethod = PaymentMethod.DEBIT` to `ExtractedExpense` (optional with default). This keeps the Telegram bot flow intact — bot-created expenses will default to `"debit"` until the LLM prompt is updated to extract payment method.

**API schemas (`src/v2/adapters/primary/bff/routers/transactions.py`):**

- `TransactionCreate`: add `payment_method: Literal["credit", "debit"]` (required, no default)
- `TransactionUpdate`: add `payment_method: Literal["credit", "debit"] | None = None`

Matches existing pattern for `transaction_type`.

**Commands:**

- `CreateExpenseCommand`: add `payment_method: str`; also widen `entry_type` from `Literal["image", "text", "pdf"]` to `str` so `"manual"` is accepted
- `UpdateExpenseCommand`: add `payment_method: str | None = None`

**Use cases:**

- `CreateExpense.execute()`: pass `payment_method` through to the repository
- `UpdateExpense.execute()`: apply `payment_method` if present

**Repository (`src/v2/adapters/secondary/supabase/expense_repository.py`):**

- Include `payment_method` in `INSERT` payload for `save()`
- Include `payment_method` in `UPDATE` payload for `update()` when present

### Frontend

**`src/lib/api.ts`:**

- `Expense` interface: add `payment_method: "credit" | "debit"`
- `ExpenseInput` interface: add `payment_method: "credit" | "debit"`

**`src/components/expenses/ExpenseModal.tsx`:**

- Add `PAYMENT_METHOD_OPTIONS`: `[{ value: "debit", label: "Debit" }, { value: "credit", label: "Credit" }]`
- Add `payment_method: "debit"` to `DEFAULT_FORM`
- Add a `<Select>` for payment method in the form grid (alongside the existing Type select)
- Populate from expense when editing

**`src/components/expenses/ExpenseTable.tsx`:**

- Add a "Payment" column displaying "Credit" or "Debit"

---

## Feature 2: Entry Type Removal

### Goal

The `entry_type` field was originally designed for Telegram bot inputs (`image`, `text`, `pdf`). When creating expenses from the web frontend it is meaningless to the user. It should be hidden and auto-set to `"manual"` to distinguish REST-created entries.

### Backend

No changes required. `TransactionCreate.entry_type: str` already accepts any string value. The value `"manual"` will be stored as-is, naturally distinguishing frontend entries from bot entries.

### Frontend

**`src/components/expenses/ExpenseModal.tsx`:**

- Remove `TIPO_OPTIONS` constant
- Remove the Entry type `<Select>` element from the form JSX
- Change `DEFAULT_FORM.entry_type` from `"text"` to `"manual"`
- Remove `entry_type` validation from `validate()` (the `if (!form.entry_type)` check)

`ExpenseInput.entry_type` stays in the interface and is still sent to the backend — it just isn't user-editable.

---

## Feature 3: Categories Bug Fix

### Root Cause

`SupabaseCategoryRepository.list_all()` (line 52 of `category_repository.py`) has an erroneous `.eq("is_active", True)` filter. The method is named `list_all` but only returns active categories, so the Categories page never receives inactive ones and users cannot re-enable them.

Additionally, `CategoryList.tsx` shows an inactive section but provides no action to re-activate a category.

### Backend Fix

**`src/v2/adapters/secondary/supabase/category_repository.py`:**

Remove `.eq("is_active", True)` from `list_all()`. The query should select all rows without filtering.

No use case or API changes needed — `ListCategories` already calls `list_all()`, and the `PATCH /api/v2/categories/{id}` endpoint already supports `{ is_active: true }` via `UpdateCategoryCommand`.

### Frontend Fix

**`src/components/categories/CategoryList.tsx`:**

Add an "Activate" button to each row in the inactive section:

```tsx
<Button
  variant="ghost"
  size="sm"
  onClick={() => handleActivate(cat)}
>
  Activate
</Button>
```

`handleActivate` calls `updateCategory(cat.id, { is_active: true })` and updates local state by setting `is_active: true` on the matching category.

---

## Scope Boundaries

- No filtering by payment method in the expenses list (not requested)
- Telegram bot flow is not broken: `ExtractedExpense.payment_method` defaults to `"debit"`. LLM prompt extraction of payment method is out of scope for this batch.
- Entry type is still stored and visible in existing data; only hidden from the create/edit UI

---

## Parallelization

All three features are independent — no shared state, no overlapping files except `src/lib/api.ts` (Features 1 and 2 both touch it). Each should be implemented on its own branch and worktree, then merged sequentially.

Feature 2 and Feature 3 each touch `api.ts` in different ways (adding a field vs no change to that file). Merge conflicts are minimal and resolvable.
