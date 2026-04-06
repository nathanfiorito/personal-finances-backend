from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from src.routers.deps import get_current_user
from src.services import database

router = APIRouter(prefix="/api/categories", tags=["categories"])


class CategoryOut(BaseModel):
    id: int
    nome: str
    ativo: bool


class CategoryCreate(BaseModel):
    nome: str


class CategoryUpdate(BaseModel):
    nome: str | None = None
    ativo: bool | None = None


@router.get("", response_model=list[CategoryOut])
async def list_categories(_user=Depends(get_current_user)):
    return await database.get_all_categories()


@router.post("", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
async def create_category(body: CategoryCreate, _user=Depends(get_current_user)):
    try:
        return await database.create_category_full(body.nome)
    except Exception as e:
        if "duplicate" in str(e).lower() or "unique" in str(e).lower():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Categoria já existe")
        raise


@router.patch("/{category_id}", response_model=CategoryOut)
async def update_category(
    category_id: int, body: CategoryUpdate, _user=Depends(get_current_user)
):
    data = body.model_dump(exclude_none=True)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Nenhum campo para atualizar",
        )
    result = await database.update_category(category_id, data)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoria não encontrada")
    return result


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_category(category_id: int, _user=Depends(get_current_user)):
    deactivated = await database.deactivate_category(category_id)
    if not deactivated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoria não encontrada")
