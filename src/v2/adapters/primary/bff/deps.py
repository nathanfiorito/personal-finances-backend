from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.v2.domain.exceptions import (
    CategoryNotFoundError,
    DomainError,
    ExpenseNotFoundError,
)

_bearer = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> dict:
    """Validate Supabase JWT. Returns the decoded payload.

    Delegates to the same logic as v1's deps.py to avoid duplication.
    """
    from src.routers.deps import get_current_user as _v1_get_current_user
    return await _v1_get_current_user(credentials)


def domain_exception_handler(exc: DomainError) -> HTTPException:
    """Map domain exceptions to HTTP status codes."""
    if isinstance(exc, (ExpenseNotFoundError, CategoryNotFoundError)):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        )
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
    )


# ── Use-case accessors (read from app.state) ──────────────────────────────────

def _uc(request: Request):
    return request.app.state.use_cases


def get_create_expense(request: Request):
    return _uc(request).create_expense


def get_list_expenses(request: Request):
    return _uc(request).list_expenses


def get_get_expense(request: Request):
    return _uc(request).get_expense


def get_update_expense(request: Request):
    return _uc(request).update_expense


def get_delete_expense(request: Request):
    return _uc(request).delete_expense


def get_list_categories(request: Request):
    return _uc(request).list_categories


def get_create_category(request: Request):
    return _uc(request).create_category


def get_update_category(request: Request):
    return _uc(request).update_category


def get_deactivate_category(request: Request):
    return _uc(request).deactivate_category


def get_get_summary(request: Request):
    return _uc(request).get_summary


def get_get_monthly(request: Request):
    return _uc(request).get_monthly


def get_export_csv(request: Request):
    return _uc(request).export_csv
