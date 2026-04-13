# Categories Bug Fix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the bug where disabled categories do not appear on the Categories page (making re-activation impossible). Root cause: `list_all()` in the Supabase repository incorrectly filters to active-only. Also add an "Activate" button to the inactive categories section.

**Architecture:** One-line backend fix (remove erroneous `.eq("is_active", True)` from `list_all()`). Frontend adds an `handleActivate` function and "Activate" button that calls the existing `PATCH /api/v2/categories/{id}` endpoint with `{ is_active: true }`. No new API endpoints needed.

**Tech Stack:** Python 3.12+, Supabase (PostgreSQL), pytest, Next.js 16, React 19, TypeScript, Vitest

---

## Files

| Action | Path |
|---|---|
| Modify | `personal-finances-backend/src/v2/adapters/secondary/supabase/category_repository.py` |
| Modify | `personal-finances-backend/tests/v2/adapters/test_bff_categories.py` |
| Modify | `personal-finances-frontend/src/components/categories/CategoryList.tsx` |

---

### Task 1: Fix list_all() in the Supabase category repository

**Files:**
- Modify: `personal-finances-backend/src/v2/adapters/secondary/supabase/category_repository.py`
- Test: `personal-finances-backend/tests/v2/adapters/test_bff_categories.py`

- [ ] **Step 1: Write a failing test proving inactive categories are returned**

In `tests/v2/adapters/test_bff_categories.py`, update `StubListCategories` to return a mix of active and inactive categories, and add a test:

```python
class StubListCategoriesAll:
    """Returns both active and inactive categories."""
    async def execute(self):
        return [
            Category(id=1, name="Alimentação", is_active=True),
            Category(id=2, name="Transporte", is_active=True),
            Category(id=3, name="Lazer", is_active=False),
        ]


def test_list_categories_includes_inactive():
    uc = SimpleNamespace(
        list_categories=StubListCategoriesAll(),
        create_category=StubCreateCategory(),
        update_category=StubUpdateCategory(),
        deactivate_category=StubDeactivateCategory(),
    )
    client = TestClient(_app(uc))
    resp = client.get("/api/v2/categories")
    assert resp.status_code == 200
    names = [c["name"] for c in resp.json()]
    assert "Lazer" in names
    inactive = [c for c in resp.json() if not c["is_active"]]
    assert len(inactive) == 1
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd personal-finances-backend
pytest tests/v2/adapters/test_bff_categories.py::test_list_categories_includes_inactive -v
```

Expected: `FAILED` — the stub returns the right data but this test validates the contract; run it to confirm the test infrastructure is sound. (This test will pass since it uses a stub. The real fix is in the repository — see note below.)

> **Note:** The actual bug is in `SupabaseCategoryRepository.list_all()`, not in the use case or router. The router and use case are correct. This test validates that the router correctly propagates whatever the use case returns. The integration fix is in Step 3.

- [ ] **Step 3: Fix the repository query**

In `src/v2/adapters/secondary/supabase/category_repository.py`, update `list_all()` — remove the `.eq("is_active", True)` filter:

```python
async def list_all(self) -> list[Category]:
    t = time.perf_counter()
    response = (
        await self._client.table(_TABLE)
        .select("id, name, is_active")
        .order("name")
        .execute()
    )
    logger.info(
        "DB %s.list_all %.0fms", _TABLE, (time.perf_counter() - t) * 1000
    )
    return [Category(**row) for row in response.data]
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
git add src/v2/adapters/secondary/supabase/category_repository.py tests/v2/adapters/test_bff_categories.py
git commit -m "fix: list_all() now returns all categories including inactive ones"
```

---

### Task 2: Add Activate button to CategoryList

**Files:**
- Modify: `personal-finances-frontend/src/components/categories/CategoryList.tsx`

- [ ] **Step 1: Add activating state and handleActivate function**

In `src/components/categories/CategoryList.tsx`, add state for the activate flow (after the `deactivating` state declaration):

```typescript
// Activate
const [activatingId, setActivatingId] = useState<number | null>(null);
```

Add the `handleActivate` function (after `handleDeactivate`):

```typescript
// ─── Activate ─────────────────────────────────────────────────────────────

const handleActivate = async (cat: CategoryOut) => {
  setActivatingId(cat.id);
  try {
    const updated = await updateCategory(cat.id, { is_active: true });
    setCategories((prev) =>
      prev.map((c) => (c.id === updated.id ? updated : c))
    );
    showToast(`Category "${cat.name}" activated`, "success");
  } catch (err) {
    const msg = err instanceof Error ? err.message : "Error activating category";
    showToast(msg, "error");
  } finally {
    setActivatingId(null);
  }
};
```

- [ ] **Step 2: Add Activate button to the inactive list**

Replace the inactive category list item JSX (the `{inactive.map(...)}` block) with:

```tsx
{inactive.map((cat) => (
  <li key={cat.id} className="flex items-center justify-between px-4 py-3 opacity-60">
    <div className="flex items-center gap-3">
      <span className="h-3 w-3 rounded-full bg-neutral-300 dark:bg-dark-border flex-shrink-0" />
      <span className="text-sm text-neutral-500 dark:text-dark-muted line-through">
        {cat.name}
      </span>
    </div>
    <Button
      variant="ghost"
      size="sm"
      onClick={() => handleActivate(cat)}
      loading={activatingId === cat.id}
    >
      Activate
    </Button>
  </li>
))}
```

- [ ] **Step 3: Run frontend tests**

```bash
cd personal-finances-frontend
npm run test -- --run
```

Expected: all tests pass (no existing tests cover CategoryList, so this is a smoke check).

- [ ] **Step 4: Lint**

```bash
cd personal-finances-frontend
npm run lint
```

Expected: no errors.

- [ ] **Step 5: Commit**

```bash
cd personal-finances-frontend
git add src/components/categories/CategoryList.tsx
git commit -m "fix: add Activate button to inactive categories so they can be re-enabled"
```
