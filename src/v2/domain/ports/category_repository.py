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
