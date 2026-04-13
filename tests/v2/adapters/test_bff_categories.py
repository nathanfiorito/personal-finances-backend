from __future__ import annotations

from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.v2.adapters.primary.bff.routers.categories import router
from src.v2.domain.entities.category import Category
from src.v2.domain.exceptions import CategoryNotFoundError


def _app(use_cases: SimpleNamespace) -> FastAPI:
    app = FastAPI()
    app.state.use_cases = use_cases
    from src.v2.adapters.primary.bff import deps
    app.dependency_overrides[deps.get_current_user] = lambda: {"sub": "test-user"}
    app.include_router(router)
    return app


class StubListCategories:
    async def execute(self):
        return [
            Category(id=1, name="Alimentação", is_active=True),
            Category(id=2, name="Transporte", is_active=True),
        ]


class StubCreateCategory:
    async def execute(self, cmd):
        return Category(id=3, name=cmd.name, is_active=True)


class StubUpdateCategory:
    def __init__(self, found: bool = True):
        self._found = found

    async def execute(self, cmd):
        if not self._found:
            raise CategoryNotFoundError("not found")
        return Category(id=cmd.category_id, name=cmd.name or "Updated", is_active=True)


class StubDeactivateCategory:
    def __init__(self, found: bool = True):
        self._found = found

    async def execute(self, cmd):
        if not self._found:
            raise CategoryNotFoundError("not found")


def _default_uc():
    return SimpleNamespace(
        list_categories=StubListCategories(),
        create_category=StubCreateCategory(),
        update_category=StubUpdateCategory(),
        deactivate_category=StubDeactivateCategory(),
    )


def test_list_categories_returns_200():
    client = TestClient(_app(_default_uc()))
    resp = client.get("/api/v2/categories")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_create_category_returns_201():
    client = TestClient(_app(_default_uc()))
    resp = client.post("/api/v2/categories", json={"name": "Pets"})
    assert resp.status_code == 201
    assert resp.json()["name"] == "Pets"


def test_update_category_returns_200():
    client = TestClient(_app(_default_uc()))
    resp = client.patch("/api/v2/categories/1", json={"name": "Comida"})
    assert resp.status_code == 200


def test_update_category_returns_404_when_not_found():
    uc = SimpleNamespace(
        create_category=StubCreateCategory(),
        update_category=StubUpdateCategory(found=False),
        deactivate_category=StubDeactivateCategory(),
    )
    client = TestClient(_app(uc))
    resp = client.patch("/api/v2/categories/999", json={"name": "X"})
    assert resp.status_code == 404


def test_delete_category_returns_204():
    client = TestClient(_app(_default_uc()))
    resp = client.delete("/api/v2/categories/1")
    assert resp.status_code == 204
