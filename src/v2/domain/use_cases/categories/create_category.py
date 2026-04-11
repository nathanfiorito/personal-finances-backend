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
