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
