from src.v2.domain.entities.category import Category
from src.v2.domain.ports.category_repository import CategoryRepository


class ListCategories:
    def __init__(self, repo: CategoryRepository) -> None:
        self._repo = repo

    async def execute(self) -> list[Category]:
        return await self._repo.list_all()
