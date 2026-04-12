# Hexagonal Architecture — Phase 3: Secondary Adapters

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement all secondary (driven) adapters: Supabase repositories, OpenRouter LLM adapter, Telegram notifier, and in-memory pending state. Each adapter implements the corresponding port ABC from Phase 1.

**Architecture:** Secondary adapters live in `src/v2/adapters/secondary/`. They are the only place that imports Supabase, OpenAI SDK, or httpx. The `domain-no-adapters` contract ensures the domain never reaches into this layer.

**Tech Stack:** Python 3.12, supabase-py (async), openai (OpenRouter-compatible), httpx, pytest

**Prerequisite:** Phase 2 complete. All domain tests pass.

**Spec:** `docs/superpowers/specs/2026-04-11-hexagonal-architecture-design.md`

---

## File Map

**Create:**
- `src/v2/adapters/secondary/supabase/expense_repository.py`
- `src/v2/adapters/secondary/supabase/category_repository.py`
- `src/v2/adapters/secondary/openrouter/llm_adapter.py`
- `src/v2/adapters/secondary/telegram_api/notifier_adapter.py`
- `src/v2/adapters/secondary/memory/pending_state_adapter.py`
- `tests/v2/adapters/__init__.py`
- `tests/v2/adapters/test_pending_state_adapter.py`
- `tests/v2/adapters/test_notifier_adapter.py`

**Note:** The Supabase and OpenRouter adapters are not unit-tested here — they are covered by existing integration tests in `tests/test_database.py` and `tests/test_extractor.py`. A smoke test in Phase 4 validates end-to-end wiring.

---

## Task 10: Supabase expense repository

**Files:**
- Create: `src/v2/adapters/secondary/supabase/expense_repository.py`

- [ ] **Step 1: Create `src/v2/adapters/secondary/supabase/expense_repository.py`**

This migrates query logic from `src/services/database.py`, scoped to expenses only, behind the `ExpenseRepository` port.

```python
import logging
import time
from datetime import date
from decimal import Decimal
from uuid import UUID

from supabase import AsyncClient

from src.v2.domain.entities.expense import Expense, ExtractedExpense
from src.v2.domain.ports.expense_repository import (
    ExpenseFilters,
    ExpenseRepository,
    ExpenseUpdate,
)

logger = logging.getLogger(__name__)

_TABLE = "transactions"


def _parse_row(row: dict) -> Expense:
    row = dict(row)
    categories_data = row.pop("categories", None)
    row["category"] = categories_data["name"] if categories_data else ""
    return Expense(**row)


class SupabaseExpenseRepository(ExpenseRepository):
    def __init__(self, client: AsyncClient) -> None:
        self._client = client

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
            "confidence": expense.confidence,
            "raw_data": {},
        }
        t = time.perf_counter()
        response = (
            await self._client.table(_TABLE)
            .insert(record)
            .select("*, categories(name)")
            .execute()
        )
        logger.info("DB %s.insert %.0fms", _TABLE, (time.perf_counter() - t) * 1000)
        return _parse_row(response.data[0])

    async def get_by_id(self, expense_id: UUID) -> Expense | None:
        t = time.perf_counter()
        response = (
            await self._client.table(_TABLE)
            .select("*, categories(name)")
            .eq("id", str(expense_id))
            .limit(1)
            .execute()
        )
        logger.info("DB %s.get_by_id %.0fms", _TABLE, (time.perf_counter() - t) * 1000)
        if not response.data:
            return None
        return _parse_row(response.data[0])

    async def list_paginated(
        self, filters: ExpenseFilters
    ) -> tuple[list[Expense], int]:
        query = self._client.table(_TABLE).select(
            "*, categories(name)", count="exact"
        )
        if filters.start:
            query = query.gte("date", filters.start.isoformat())
        if filters.end:
            query = query.lte("date", filters.end.isoformat())
        if filters.category_id is not None:
            query = query.eq("category_id", filters.category_id)
        if filters.transaction_type is not None:
            query = query.eq("transaction_type", filters.transaction_type)
        offset = (filters.page - 1) * filters.page_size
        query = query.order("date", desc=True).range(
            offset, offset + filters.page_size - 1
        )
        t = time.perf_counter()
        response = await query.execute()
        logger.info(
            "DB %s.list_paginated(page=%d) %.0fms",
            _TABLE, filters.page, (time.perf_counter() - t) * 1000,
        )
        total = response.count or 0
        return [_parse_row(row) for row in response.data], total

    async def list_by_period(
        self,
        start: date,
        end: date,
        transaction_type: str | None = None,
    ) -> list[Expense]:
        query = (
            self._client.table(_TABLE)
            .select("*, categories(name)")
            .gte("date", start.isoformat())
            .lte("date", end.isoformat())
        )
        if transaction_type is not None:
            query = query.eq("transaction_type", transaction_type)
        t = time.perf_counter()
        response = await query.order("date").execute()
        logger.info(
            "DB %s.list_by_period(%s..%s) %.0fms",
            _TABLE, start, end, (time.perf_counter() - t) * 1000,
        )
        return [_parse_row(row) for row in response.data]

    async def get_recent(self, limit: int = 3) -> list[Expense]:
        t = time.perf_counter()
        response = (
            await self._client.table(_TABLE)
            .select("*, categories(name)")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        logger.info(
            "DB %s.get_recent(limit=%d) %.0fms",
            _TABLE, limit, (time.perf_counter() - t) * 1000,
        )
        return [_parse_row(row) for row in response.data]

    async def update(self, expense_id: UUID, data: ExpenseUpdate) -> Expense | None:
        payload = {
            k: v
            for k, v in {
                "amount": data.amount,
                "date": data.date.isoformat() if data.date else None,
                "establishment": data.establishment,
                "description": data.description,
                "category_id": data.category_id,
                "tax_id": data.tax_id,
                "entry_type": data.entry_type,
                "transaction_type": data.transaction_type,
            }.items()
            if v is not None
        }
        if not payload:
            return await self.get_by_id(expense_id)
        t = time.perf_counter()
        response = (
            await self._client.table(_TABLE)
            .update(payload)
            .eq("id", str(expense_id))
            .select("*, categories(name)")
            .execute()
        )
        logger.info(
            "DB %s.update %.0fms", _TABLE, (time.perf_counter() - t) * 1000
        )
        if not response.data:
            return None
        return _parse_row(response.data[0])

    async def delete(self, expense_id: UUID) -> bool:
        t = time.perf_counter()
        response = (
            await self._client.table(_TABLE)
            .delete()
            .eq("id", str(expense_id))
            .select("id")
            .execute()
        )
        logger.info(
            "DB %s.delete %.0fms", _TABLE, (time.perf_counter() - t) * 1000
        )
        return bool(response.data)
```

- [ ] **Step 2: Run arch test — must still pass**

```bash
pytest tests/v2/test_architecture.py -v
```

Expected: `PASSED`

- [ ] **Step 3: Commit**

```bash
git add src/v2/adapters/secondary/supabase/expense_repository.py
git commit -m "feat(v2): add SupabaseExpenseRepository adapter"
```

---

## Task 11: Supabase category repository

**Files:**
- Create: `src/v2/adapters/secondary/supabase/category_repository.py`

- [ ] **Step 1: Create `src/v2/adapters/secondary/supabase/category_repository.py`**

The 5-minute cache is an implementation detail of this adapter — invisible to the domain.

```python
import logging
import time

from supabase import AsyncClient

from src.v2.domain.entities.category import Category
from src.v2.domain.ports.category_repository import CategoryRepository, CategoryUpdate

logger = logging.getLogger(__name__)

_TABLE = "categories"
_CACHE_TTL = 300  # 5 minutes


class SupabaseCategoryRepository(CategoryRepository):
    def __init__(self, client: AsyncClient) -> None:
        self._client = client
        self._active_names_cache: list[str] | None = None
        self._cache_expires_at: float = 0.0

    def _invalidate_cache(self) -> None:
        self._active_names_cache = None
        self._cache_expires_at = 0.0

    async def list_active(self) -> list[str]:
        if (
            self._active_names_cache is not None
            and time.monotonic() < self._cache_expires_at
        ):
            return self._active_names_cache

        t = time.perf_counter()
        response = (
            await self._client.table(_TABLE)
            .select("name")
            .eq("is_active", True)
            .order("name")
            .execute()
        )
        logger.info(
            "DB %s.list_active %.0fms", _TABLE, (time.perf_counter() - t) * 1000
        )
        names = [row["name"] for row in response.data]
        self._active_names_cache = names
        self._cache_expires_at = time.monotonic() + _CACHE_TTL
        return names

    async def list_all(self) -> list[Category]:
        t = time.perf_counter()
        response = (
            await self._client.table(_TABLE)
            .select("id, name, is_active")
            .eq("is_active", True)
            .order("name")
            .execute()
        )
        logger.info(
            "DB %s.list_all %.0fms", _TABLE, (time.perf_counter() - t) * 1000
        )
        return [Category(**row) for row in response.data]

    async def create(self, name: str) -> Category:
        t = time.perf_counter()
        response = (
            await self._client.table(_TABLE)
            .insert({"name": name})
            .select("id, name, is_active")
            .execute()
        )
        logger.info(
            "DB %s.create %.0fms", _TABLE, (time.perf_counter() - t) * 1000
        )
        self._invalidate_cache()
        return Category(**response.data[0])

    async def update(self, category_id: int, data: CategoryUpdate) -> Category | None:
        payload = {k: v for k, v in {"name": data.name, "is_active": data.is_active}.items()
                   if v is not None}
        if not payload:
            return None
        t = time.perf_counter()
        response = (
            await self._client.table(_TABLE)
            .update(payload)
            .eq("id", category_id)
            .select("id, name, is_active")
            .execute()
        )
        logger.info(
            "DB %s.update %.0fms", _TABLE, (time.perf_counter() - t) * 1000
        )
        self._invalidate_cache()
        if not response.data:
            return None
        return Category(**response.data[0])

    async def deactivate(self, category_id: int) -> bool:
        t = time.perf_counter()
        response = (
            await self._client.table(_TABLE)
            .update({"is_active": False})
            .eq("id", category_id)
            .select("id")
            .execute()
        )
        logger.info(
            "DB %s.deactivate %.0fms", _TABLE, (time.perf_counter() - t) * 1000
        )
        self._invalidate_cache()
        return bool(response.data)
```

- [ ] **Step 2: Run arch test**

```bash
pytest tests/v2/test_architecture.py -v
```

Expected: `PASSED`

- [ ] **Step 3: Commit**

```bash
git add src/v2/adapters/secondary/supabase/category_repository.py
git commit -m "feat(v2): add SupabaseCategoryRepository adapter with 5-min cache"
```

---

## Task 12: OpenRouter LLM adapter

**Files:**
- Create: `src/v2/adapters/secondary/openrouter/llm_adapter.py`

This consolidates the logic from `src/agents/extractor.py`, `src/agents/categorizer.py`, `src/agents/duplicate_checker.py`, and `src/agents/reporter.py` into a single class behind the `LLMPort`.

- [ ] **Step 1: Create `src/v2/adapters/secondary/openrouter/llm_adapter.py`**

```python
import base64
import json
import logging
import re
from decimal import Decimal, InvalidOperation

from openai import AsyncOpenAI

from src.v2.domain.entities.expense import Expense, ExtractedExpense
from src.v2.domain.ports.llm_port import LLMPort
# Re-use the existing retry-aware chat_completion helper to avoid duplicating
# exponential back-off logic.
from src.services.llm import chat_completion

logger = logging.getLogger(__name__)


class OpenRouterLLMAdapter(LLMPort):
    """Implements LLMPort using OpenRouter (OpenAI-compatible API)."""

    def __init__(self, model_vision: str, model_fast: str) -> None:
        """
        Args:
            model_vision: Model ID for image extraction and reports
                          e.g. "anthropic/claude-sonnet-4-6"
            model_fast:   Model ID for text extraction, categorization,
                          and duplicate checking
                          e.g. "anthropic/claude-haiku-4-5"
        """
        self._model_vision = model_vision
        self._model_fast = model_fast

    # ── Extraction ────────────────────────────────────────────────────────────

    async def extract_from_image(self, image_b64: str) -> ExtractedExpense:
        prompt = _PROMPT_IMAGE
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"},
                    },
                ],
            }
        ]
        raw = await chat_completion(
            model=self._model_vision, messages=messages, max_tokens=500
        )
        return _parse_extracted(raw, entry_type="image")

    async def extract_from_text(self, text: str) -> ExtractedExpense:
        prompt = _PROMPT_TEXT.format(texto=text)
        messages = [{"role": "user", "content": prompt}]
        raw = await chat_completion(
            model=self._model_fast, messages=messages, max_tokens=300
        )
        return _parse_extracted(raw, entry_type="text")

    # ── Categorization ────────────────────────────────────────────────────────

    async def categorize(
        self, expense: ExtractedExpense, categories: list[str]
    ) -> str:
        prompt = _PROMPT_CATEGORIZE.format(
            categories=", ".join(categories),
            establishment=expense.establishment or "Não informado",
            description=expense.description or "Não informada",
        )
        raw = await chat_completion(
            model=self._model_fast,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=20,
        )
        category = raw.strip().rstrip(".")
        if category in categories:
            return category
        # Case-insensitive fallback
        for cat in categories:
            if cat.lower() == category.lower():
                return cat
        logger.warning("LLM returned unknown category %r — defaulting to Outros", category)
        return "Outros" if "Outros" in categories else categories[0]

    # ── Duplicate check ───────────────────────────────────────────────────────

    async def check_duplicate(
        self, expense: ExtractedExpense, recent: list[Expense]
    ) -> str | None:
        if not recent:
            return None
        recent_lines = "\n".join(
            f"- {e.date} | R${e.amount} | {e.establishment or 'N/A'} | {e.category}"
            for e in recent
        )
        new_line = (
            f"- {expense.date} | R${expense.amount} "
            f"| {expense.establishment or 'N/A'}"
        )
        prompt = _PROMPT_DUPLICATE.format(
            recent=recent_lines, new_expense=new_line
        )
        raw = await chat_completion(
            model=self._model_fast,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100,
        )
        raw = raw.strip()
        if raw.upper().startswith("DUPLICATA"):
            reason = raw[len("DUPLICATA"):].strip(" :-")
            return reason or "Despesa similar encontrada recentemente."
        return None

    # ── Report ────────────────────────────────────────────────────────────────

    async def generate_report(
        self, expenses: list[Expense], period: str
    ) -> str:
        from decimal import Decimal
        totals: dict[str, Decimal] = {}
        for expense in expenses:
            totals[expense.category] = (
                totals.get(expense.category, Decimal("0")) + expense.amount
            )
        summary_lines = [
            f"- {cat}: R${total:.2f}" for cat, total in sorted(totals.items())
        ]
        prompt = _PROMPT_REPORT.format(
            period=period, summary="\n".join(summary_lines)
        )
        raw = await chat_completion(
            model=self._model_vision,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=120,
        )
        return raw.strip()


# ── Prompts ───────────────────────────────────────────────────────────────────

_PROMPT_IMAGE = """Analyze this Brazilian payment receipt and extract the information in the JSON format below.
Return ONLY the JSON, no additional text, no markdown, no explanations.

{
  "amount": <positive decimal number, e.g.: 45.90>,
  "date": "<transaction date in ISO 8601, e.g.: 2024-01-15>",
  "establishment": "<establishment name or null>",
  "description": "<short payment description or null>",
  "tax_id": "<establishment CNPJ tax ID or null>",
  "transaction_type": "<\"income\" for money coming in or \"outcome\" for money going out. When in doubt, use \"outcome\">",
  "confidence": <number between 0.0 and 1.0>
}

Rules:
- amount: use the TOTAL transaction value. Brazilian comma (45,90) becomes decimal point (45.90).
- date: use the transaction date, not the issue date. If ambiguous prefer Brazilian format (dd/mm).
- establishment: commercial name, not legal entity name.
- If a field is not legible or does not exist, use null."""

_PROMPT_TEXT = """Extract the financial information from the message below and return ONLY a JSON, no additional text.

{{
  "amount": <positive decimal number, e.g.: 45.90>,
  "date": "<date in ISO 8601 or null if not mentioned>",
  "establishment": "<place/establishment name or null>",
  "description": "<description of what was purchased/paid/received or null>",
  "tax_id": null,
  "transaction_type": "<\"income\" for money coming in or \"outcome\" for money going out. When in doubt, use \"outcome\">",
  "confidence": <0.0 to 1.0>
}}

Rules:
- If the date is not mentioned, use null (do not invent a date).
- Values like "50 reais", "R$ 50", "50,00" or "50" should become 50.0.
- confidence: the clearer the message, the higher.

Message: "{texto}" """

_PROMPT_CATEGORIZE = """Classifique a despesa abaixo em UMA das categorias: {categories}

Estabelecimento: {establishment}
Descrição: {description}

Responda APENAS com o nome exato da categoria, sem explicação."""

_PROMPT_DUPLICATE = """Compare the new expense with the recent expenses below.

Recent expenses:
{recent}

New expense:
{new_expense}

If the new expense appears to be a duplicate of one of the recent ones (same store, similar amount, same or consecutive days), respond with:
DUPLICATA: <brief reason in Portuguese>

If it is NOT a duplicate, respond with:
OK"""

_PROMPT_REPORT = """Você é um assistente financeiro pessoal. Analise o resumo de despesas abaixo e gere exatamente 2 frases de insight financeiro em português. Seja direto e útil.

Período: {period}
Despesas por categoria:
{summary}

Responda com exatamente 2 frases."""


# ── JSON parsing helpers ──────────────────────────────────────────────────────

def _parse_extracted(raw: str, entry_type: str) -> ExtractedExpense:
    data = _parse_llm_json(raw)
    try:
        amount = Decimal(str(data.get("amount", 0)))
    except InvalidOperation:
        amount = Decimal("0.01")

    from datetime import date as _date
    raw_date = data.get("date")
    parsed_date: _date | None = None
    if raw_date:
        try:
            from datetime import datetime
            parsed_date = datetime.fromisoformat(str(raw_date)).date()
        except (ValueError, TypeError):
            parsed_date = None

    return ExtractedExpense(
        amount=amount,
        date=parsed_date,
        establishment=data.get("establishment"),
        description=data.get("description"),
        tax_id=data.get("tax_id"),
        entry_type=entry_type,  # type: ignore[arg-type]
        transaction_type=data.get("transaction_type", "outcome"),  # type: ignore[arg-type]
        confidence=float(data.get("confidence", 0.5)),
    )


def _parse_llm_json(raw: str) -> dict:
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    logger.warning("Could not parse LLM JSON: %r", raw[:200])
    return {}
```

- [ ] **Step 2: Run arch test**

```bash
pytest tests/v2/test_architecture.py -v
```

Expected: `PASSED`

- [ ] **Step 3: Commit**

```bash
git add src/v2/adapters/secondary/openrouter/llm_adapter.py
git commit -m "feat(v2): add OpenRouterLLMAdapter (consolidates 4 agents into one port impl)"
```

---

## Task 13: Telegram notifier adapter

**Files:**
- Create: `src/v2/adapters/secondary/telegram_api/notifier_adapter.py`
- Create: `tests/v2/adapters/__init__.py`
- Create: `tests/v2/adapters/test_notifier_adapter.py`

- [ ] **Step 1: Write `tests/v2/adapters/test_notifier_adapter.py`**

These tests use `unittest.mock` to patch the underlying httpx calls — no real Telegram API required.

```python
from unittest.mock import AsyncMock, patch

import pytest

from src.v2.adapters.secondary.telegram_api.notifier_adapter import (
    TelegramNotifierAdapter,
)
from src.v2.domain.ports.notifier_port import NotificationButton


@pytest.fixture
def adapter():
    return TelegramNotifierAdapter(
        bot_token="test-token", base_url="https://api.telegram.org"
    )


@pytest.mark.asyncio
async def test_send_message_calls_telegram_api(adapter):
    with patch(
        "src.v2.adapters.secondary.telegram_api.notifier_adapter._post",
        new_callable=AsyncMock,
    ) as mock_post:
        mock_post.return_value = None
        await adapter.send_message(chat_id=123, text="Hello")
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert "sendMessage" in call_args[0][0]
        assert call_args[1]["json"]["chat_id"] == 123
        assert call_args[1]["json"]["text"] == "Hello"


@pytest.mark.asyncio
async def test_send_message_with_buttons_builds_inline_keyboard(adapter):
    with patch(
        "src.v2.adapters.secondary.telegram_api.notifier_adapter._post",
        new_callable=AsyncMock,
    ) as mock_post:
        mock_post.return_value = None
        buttons = [
            [NotificationButton(text="Yes", callback_data="yes")],
            [NotificationButton(text="No", callback_data="no")],
        ]
        await adapter.send_message(chat_id=123, text="Choose", buttons=buttons)
        payload = mock_post.call_args[1]["json"]
        keyboard = payload["reply_markup"]["inline_keyboard"]
        assert keyboard[0][0]["text"] == "Yes"
        assert keyboard[0][0]["callback_data"] == "yes"
        assert keyboard[1][0]["text"] == "No"


@pytest.mark.asyncio
async def test_answer_callback_calls_correct_endpoint(adapter):
    with patch(
        "src.v2.adapters.secondary.telegram_api.notifier_adapter._post",
        new_callable=AsyncMock,
    ) as mock_post:
        mock_post.return_value = None
        await adapter.answer_callback(callback_id="cb-123", text="Done")
        call_args = mock_post.call_args
        assert "answerCallbackQuery" in call_args[0][0]
        assert call_args[1]["json"]["callback_query_id"] == "cb-123"
```

- [ ] **Step 2: Create `tests/v2/adapters/__init__.py`** (empty)

- [ ] **Step 3: Run tests — expect FAIL**

```bash
pytest tests/v2/adapters/test_notifier_adapter.py -v
```

Expected: `ImportError`

- [ ] **Step 4: Create `src/v2/adapters/secondary/telegram_api/notifier_adapter.py`**

```python
import logging
from typing import Any

import httpx

from src.v2.domain.ports.notifier_port import NotificationButton, NotifierPort

logger = logging.getLogger(__name__)


async def _post(url: str, **kwargs: Any) -> None:
    """Fire-and-forget POST to the Telegram Bot API."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(url, **kwargs)
        if not response.is_success:
            logger.warning(
                "Telegram API error %d: %s", response.status_code, response.text[:200]
            )


def _build_keyboard(
    buttons: list[list[NotificationButton]],
) -> dict:
    return {
        "inline_keyboard": [
            [{"text": btn.text, "callback_data": btn.callback_data} for btn in row]
            for row in buttons
        ]
    }


class TelegramNotifierAdapter(NotifierPort):
    def __init__(self, bot_token: str, base_url: str = "https://api.telegram.org") -> None:
        self._base = f"{base_url}/bot{bot_token}"

    async def send_message(
        self,
        chat_id: int,
        text: str,
        parse_mode: str | None = None,
        buttons: list[list[NotificationButton]] | None = None,
    ) -> None:
        payload: dict = {"chat_id": chat_id, "text": text}
        if parse_mode:
            payload["parse_mode"] = parse_mode
        if buttons:
            payload["reply_markup"] = _build_keyboard(buttons)
        await _post(f"{self._base}/sendMessage", json=payload)

    async def send_file(
        self,
        chat_id: int,
        content: bytes,
        filename: str,
        caption: str,
    ) -> None:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self._base}/sendDocument",
                data={"chat_id": chat_id, "caption": caption},
                files={"document": (filename, content, "text/csv")},
            )
            if not response.is_success:
                logger.warning(
                    "Telegram sendDocument error %d: %s",
                    response.status_code,
                    response.text[:200],
                )

    async def answer_callback(
        self,
        callback_id: str,
        text: str | None = None,
    ) -> None:
        payload: dict = {"callback_query_id": callback_id}
        if text:
            payload["text"] = text
        await _post(f"{self._base}/answerCallbackQuery", json=payload)

    async def edit_message(
        self,
        chat_id: int,
        message_id: int,
        text: str,
        parse_mode: str | None = None,
        buttons: list[list[NotificationButton]] | None = None,
    ) -> None:
        payload: dict = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
        }
        if parse_mode:
            payload["parse_mode"] = parse_mode
        if buttons:
            payload["reply_markup"] = _build_keyboard(buttons)
        else:
            payload["reply_markup"] = {"inline_keyboard": []}
        try:
            await _post(f"{self._base}/editMessageText", json=payload)
        except Exception:
            logger.warning(
                "editMessageText failed for chat_id=%s — sending new message", chat_id
            )
            await self.send_message(chat_id, text, parse_mode=parse_mode)
```

- [ ] **Step 5: Run tests — expect PASS**

```bash
pytest tests/v2/adapters/test_notifier_adapter.py -v
```

Expected: `3 passed`

- [ ] **Step 6: Run arch test**

```bash
pytest tests/v2/test_architecture.py -v
```

Expected: `PASSED`

- [ ] **Step 7: Commit**

```bash
git add src/v2/adapters/secondary/telegram_api/ tests/v2/adapters/
git commit -m "feat(v2): add TelegramNotifierAdapter with unit tests"
```

---

## Task 14: In-memory pending state adapter

**Files:**
- Create: `src/v2/adapters/secondary/memory/pending_state_adapter.py`
- Create: `tests/v2/adapters/test_pending_state_adapter.py`

- [ ] **Step 1: Write `tests/v2/adapters/test_pending_state_adapter.py`**

```python
import time

import pytest

from src.v2.domain.entities.expense import ExtractedExpense
from src.v2.domain.ports.pending_state_port import PendingExpense
from src.v2.adapters.secondary.memory.pending_state_adapter import (
    InMemoryPendingStateAdapter,
)
from decimal import Decimal
import datetime as _dt


def _make_pending(chat_id: int = 1) -> PendingExpense:
    return PendingExpense(
        extracted=ExtractedExpense(
            amount=Decimal("50.00"),
            date=_dt.date(2026, 1, 15),
            entry_type="text",
            transaction_type="outcome",
            confidence=0.9,
        ),
        category="Alimentação",
        category_id=1,
        chat_id=chat_id,
        message_id=42,
    )


def test_set_and_get_returns_state():
    adapter = InMemoryPendingStateAdapter()
    state = _make_pending(chat_id=1)
    adapter.set(1, state)
    result = adapter.get(1)
    assert result is not None
    assert result.category == "Alimentação"


def test_get_returns_none_for_unknown_chat():
    adapter = InMemoryPendingStateAdapter()
    assert adapter.get(999) is None


def test_clear_removes_state():
    adapter = InMemoryPendingStateAdapter()
    adapter.set(1, _make_pending(1))
    adapter.clear(1)
    assert adapter.get(1) is None


def test_update_category_changes_pending_category():
    adapter = InMemoryPendingStateAdapter()
    adapter.set(1, _make_pending(1))
    result = adapter.update_category(1, "Transporte", 2)
    assert result is True
    state = adapter.get(1)
    assert state.category == "Transporte"
    assert state.category_id == 2


def test_update_category_returns_false_for_unknown_chat():
    adapter = InMemoryPendingStateAdapter()
    result = adapter.update_category(999, "Transporte", 2)
    assert result is False


def test_get_returns_none_after_expiry():
    adapter = InMemoryPendingStateAdapter()
    state = _make_pending(1)
    # Force expiry by setting expires_at to the past
    state.expires_at = time.monotonic() - 1
    adapter.set(1, state)
    assert adapter.get(1) is None
```

- [ ] **Step 2: Run tests — expect FAIL**

```bash
pytest tests/v2/adapters/test_pending_state_adapter.py -v
```

Expected: `ImportError`

- [ ] **Step 3: Create `src/v2/adapters/secondary/memory/pending_state_adapter.py`**

```python
from src.v2.domain.ports.pending_state_port import PendingExpense, PendingStatePort


class InMemoryPendingStateAdapter(PendingStatePort):
    """Thread-unsafe in-memory store for pending expenses.

    Suitable for single-process deployments (Render free tier runs one worker).
    TTL is enforced lazily on `get()`.
    """

    def __init__(self) -> None:
        self._store: dict[int, PendingExpense] = {}

    def set(self, chat_id: int, state: PendingExpense) -> None:
        self._store[chat_id] = state

    def get(self, chat_id: int) -> PendingExpense | None:
        state = self._store.get(chat_id)
        if state is None:
            return None
        if state.is_expired():
            self.clear(chat_id)
            return None
        return state

    def update_category(
        self, chat_id: int, category: str, category_id: int
    ) -> bool:
        state = self.get(chat_id)
        if state is None:
            return False
        state.category = category
        state.category_id = category_id
        return True

    def clear(self, chat_id: int) -> None:
        self._store.pop(chat_id, None)
```

- [ ] **Step 4: Run tests — expect PASS**

```bash
pytest tests/v2/adapters/test_pending_state_adapter.py -v
```

Expected: `6 passed`

- [ ] **Step 5: Run full Phase 3 suite + arch test**

```bash
pytest tests/v2/ -v
```

Expected: all tests pass

- [ ] **Step 6: Commit**

```bash
git add src/v2/adapters/secondary/memory/ tests/v2/adapters/test_pending_state_adapter.py
git commit -m "feat(v2): add InMemoryPendingStateAdapter with unit tests"
```

---

## Phase 3 complete

```bash
pytest tests/v2/ -v
```

Expected: `~33 tests passed`, `0 failed`

All secondary adapters are in place. The domain is still clean — `tests/v2/test_architecture.py` passes. No adapter imports a primary adapter.

**Next:** Phase 4 — Primary Adapters + Integration (`docs/superpowers/plans/2026-04-11-hexagonal-phase4-primary-adapters.md`)
