from dataclasses import dataclass

from src.v2.domain.exceptions import CategoryNotFoundError
from src.v2.domain.ports.category_repository import CategoryRepository


@dataclass
class DeactivateCategoryCommand:
    category_id: int


class DeactivateCategory:
    def __init__(self, repo: CategoryRepository) -> None:
        self._repo = repo

    async def execute(self, cmd: DeactivateCategoryCommand) -> None:
        deactivated = await self._repo.deactivate(cmd.category_id)
        if not deactivated:
            raise CategoryNotFoundError(f"Category {cmd.category_id} not found")
