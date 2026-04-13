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
            .execute()
        )
        logger.info(
            "DB %s.create %.0fms", _TABLE, (time.perf_counter() - t) * 1000
        )
        self._invalidate_cache()
        row_id = response.data[0]["id"]
        fetch = (
            await self._client.table(_TABLE)
            .select("id, name, is_active")
            .eq("id", row_id)
            .limit(1)
            .execute()
        )
        return Category(**fetch.data[0])

    async def update(self, category_id: int, data: CategoryUpdate) -> Category | None:
        payload = {
            k: v
            for k, v in {"name": data.name, "is_active": data.is_active}.items()
            if v is not None
        }
        if not payload:
            return None
        t = time.perf_counter()
        await (
            self._client.table(_TABLE)
            .update(payload)
            .eq("id", category_id)
            .execute()
        )
        logger.info(
            "DB %s.update %.0fms", _TABLE, (time.perf_counter() - t) * 1000
        )
        self._invalidate_cache()
        fetch = (
            await self._client.table(_TABLE)
            .select("id, name, is_active")
            .eq("id", category_id)
            .limit(1)
            .execute()
        )
        if not fetch.data:
            return None
        return Category(**fetch.data[0])

    async def deactivate(self, category_id: int) -> bool:
        t = time.perf_counter()
        await (
            self._client.table(_TABLE)
            .update({"is_active": False})
            .eq("id", category_id)
            .execute()
        )
        logger.info(
            "DB %s.deactivate %.0fms", _TABLE, (time.perf_counter() - t) * 1000
        )
        self._invalidate_cache()
        fetch = (
            await self._client.table(_TABLE)
            .select("id")
            .eq("id", category_id)
            .limit(1)
            .execute()
        )
        return bool(fetch.data)
