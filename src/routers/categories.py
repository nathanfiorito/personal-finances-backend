from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from src.routers.deps import get_current_user
from src.services import database

router = APIRouter(prefix="/api/categories", tags=["categories"])


class CategoryOut(BaseModel):
    id: int
    name: str
    is_active: bool


class CategoryCreate(BaseModel):
    name: str


class CategoryUpdate(BaseModel):
    name: str | None = None
    is_active: bool | None = None


@router.get("", response_model=list[CategoryOut])
async def list_categories(_user=Depends(get_current_user)):
    return await database.get_all_categories()


@router.post("", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
async def create_category(body: CategoryCreate, _user=Depends(get_current_user)):
    try:
        return await database.create_category_full(body.name)
    except Exception as e:
        if "duplicate" in str(e).lower() or "unique" in str(e).lower():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Category already exists")  # noqa: E501
        raise


@router.patch("/{category_id}", response_model=CategoryOut)
async def update_category(
    category_id: int, body: CategoryUpdate, _user=Depends(get_current_user)
):
    data = body.model_dump(exclude_none=True)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No fields to update",
        )
    result = await database.update_category(category_id, data)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return result


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_category(category_id: int, _user=Depends(get_current_user)):
    deactivated = await database.deactivate_category(category_id)
    if not deactivated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
