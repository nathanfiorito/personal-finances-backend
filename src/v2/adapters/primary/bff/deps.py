import base64
import json
import logging
import time

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from supabase import AsyncClient, acreate_client

from src.config.settings import settings as _settings
from src.v2.domain.exceptions import (
    CategoryNotFoundError,
    DomainError,
    ExpenseNotFoundError,
)

logger = logging.getLogger(__name__)

_bearer = HTTPBearer()
_auth_client: AsyncClient | None = None


async def _get_auth_client() -> AsyncClient:
    global _auth_client
    if _auth_client is None:
        _auth_client = await acreate_client(_settings.supabase_url, _settings.supabase_service_key)
    return _auth_client


def _is_token_expired(token: str) -> bool:
    try:
        payload = token.split(".")[1]
        payload += "=" * (4 - len(payload) % 4)
        data = json.loads(base64.b64decode(payload))
        return data.get("exp", 0) < time.time()
    except Exception:
        return False


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> dict:
    """Validate Supabase JWT and return the user object."""
    token = credentials.credentials
    try:
        client = await _get_auth_client()
        response = await client.auth.get_user(token)
        return response.user
    except Exception as e:
        logger.debug("JWT validation failed: %s", e)
        if _is_token_expired(token):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Token expirado",
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
        )


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
