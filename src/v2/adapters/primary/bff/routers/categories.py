from __future__ import annotations

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel

from src.v2.adapters.primary.bff.deps import (
    domain_exception_handler,
    get_create_category,
    get_current_user,
    get_deactivate_category,
    get_list_categories,
    get_update_category,
)
from src.v2.domain.entities.category import Category
from src.v2.domain.exceptions import DomainError
from src.v2.domain.use_cases.categories.create_category import CreateCategoryCommand
from src.v2.domain.use_cases.categories.deactivate_category import DeactivateCategoryCommand
from src.v2.domain.use_cases.categories.update_category import UpdateCategoryCommand

router = APIRouter(prefix="/api/v2/categories", tags=["v2-categories"])


class CategoryCreate(BaseModel):
    name: str


class CategoryPatch(BaseModel):
    name: str | None = None
    is_active: bool | None = None


@router.get("", response_model=list[Category])
async def list_categories(
    _user=Depends(get_current_user),
    use_case=Depends(get_list_categories),
):
    return await use_case.execute()


@router.post("", response_model=Category, status_code=status.HTTP_201_CREATED)
async def create_category(
    body: CategoryCreate,
    _user=Depends(get_current_user),
    use_case=Depends(get_create_category),
):
    return await use_case.execute(CreateCategoryCommand(name=body.name))


@router.patch("/{category_id}", response_model=Category)
async def update_category(
    category_id: int,
    body: CategoryPatch,
    _user=Depends(get_current_user),
    use_case=Depends(get_update_category),
):
    try:
        return await use_case.execute(
            UpdateCategoryCommand(
                category_id=category_id,
                name=body.name,
                is_active=body.is_active,
            )
        )
    except DomainError as exc:
        raise domain_exception_handler(exc)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_category(
    category_id: int,
    _user=Depends(get_current_user),
    use_case=Depends(get_deactivate_category),
):
    try:
        await use_case.execute(DeactivateCategoryCommand(category_id=category_id))
    except DomainError as exc:
        raise domain_exception_handler(exc)
