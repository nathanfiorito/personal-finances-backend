"""Backward-compatibility layer: all /api/expenses/* routes redirect to /api/transactions/*."""
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

router = APIRouter(prefix="/api/expenses", tags=["expenses-compat"])


def _redirect(request: Request) -> RedirectResponse:
    new_path = str(request.url).replace("/api/expenses", "/api/transactions", 1)
    return RedirectResponse(url=new_path, status_code=301)


@router.api_route("", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def redirect_root(request: Request):
    return _redirect(request)


@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def redirect_with_path(path: str, request: Request):
    return _redirect(request)
