import pytest

from src.v2.domain.entities.category import Category
from src.v2.domain.exceptions import CategoryNotFoundError
from src.v2.domain.ports.category_repository import CategoryRepository, CategoryUpdate
from src.v2.domain.use_cases.categories.create_category import (
    CreateCategory,
    CreateCategoryCommand,
)
from src.v2.domain.use_cases.categories.deactivate_category import (
    DeactivateCategory,
    DeactivateCategoryCommand,
)
from src.v2.domain.use_cases.categories.list_categories import ListCategories
from src.v2.domain.use_cases.categories.update_category import (
    UpdateCategory,
    UpdateCategoryCommand,
)


class StubCategoryRepository(CategoryRepository):
    def __init__(self):
        self._categories: list[Category] = [
            Category(id=1, name="Alimentação", is_active=True),
            Category(id=2, name="Transporte", is_active=True),
        ]

    async def list_active(self) -> list[str]:
        return [c.name for c in self._categories if c.is_active]

    async def list_all(self) -> list[Category]:
        return self._categories

    async def create(self, name: str) -> Category:
        new_id = max(c.id for c in self._categories) + 1
        cat = Category(id=new_id, name=name, is_active=True)
        self._categories.append(cat)
        return cat

    async def update(self, category_id: int, data: CategoryUpdate) -> Category | None:
        for cat in self._categories:
            if cat.id == category_id:
                return Category(
                    id=cat.id,
                    name=data.name if data.name is not None else cat.name,
                    is_active=data.is_active if data.is_active is not None else cat.is_active,
                )
        return None

    async def deactivate(self, category_id: int) -> bool:
        for cat in self._categories:
            if cat.id == category_id:
                cat.is_active = False
                return True
        return False


@pytest.mark.asyncio
async def test_list_categories_returns_all():
    repo = StubCategoryRepository()
    result = await ListCategories(repo).execute()
    assert len(result) == 2
    assert result[0].name == "Alimentação"


@pytest.mark.asyncio
async def test_create_category_returns_new_category():
    repo = StubCategoryRepository()
    result = await CreateCategory(repo).execute(CreateCategoryCommand(name="Pets"))
    assert result.name == "Pets"
    assert result.is_active is True


@pytest.mark.asyncio
async def test_update_category_returns_updated():
    repo = StubCategoryRepository()
    result = await UpdateCategory(repo).execute(
        UpdateCategoryCommand(category_id=1, name="Comida")
    )
    assert result.name == "Comida"


@pytest.mark.asyncio
async def test_update_category_raises_when_not_found():
    repo = StubCategoryRepository()
    with pytest.raises(CategoryNotFoundError):
        await UpdateCategory(repo).execute(
            UpdateCategoryCommand(category_id=999, name="X")
        )


@pytest.mark.asyncio
async def test_deactivate_category_succeeds():
    repo = StubCategoryRepository()
    # Should not raise
    await DeactivateCategory(repo).execute(DeactivateCategoryCommand(category_id=1))


@pytest.mark.asyncio
async def test_deactivate_category_raises_when_not_found():
    repo = StubCategoryRepository()
    with pytest.raises(CategoryNotFoundError):
        await DeactivateCategory(repo).execute(DeactivateCategoryCommand(category_id=999))
