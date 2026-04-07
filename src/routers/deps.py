import base64
import json
import logging
import time

from fastapi import Header, HTTPException, status

from src.services.database import _get_client

logger = logging.getLogger(__name__)


def _is_token_expired(token: str) -> bool:
    """Decode JWT payload locally (without verification) to check expiration."""
    try:
        payload = token.split(".")[1]
        payload += "=" * (4 - len(payload) % 4)
        data = json.loads(base64.b64decode(payload))
        return data.get("exp", 0) < time.time()
    except Exception:
        return False


async def get_current_user(authorization: str | None = Header(default=None, alias="Authorization")):
    """FastAPI dependency that validates a Supabase JWT and returns the user."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token ausente ou malformado",
        )
    token = authorization.removeprefix("Bearer ")
    try:
        client = await _get_client()
        response = await client.auth.get_user(token)
        return response.user
    except Exception as e:
        logger.debug("Falha na validação do JWT: %s", e)
        # TODO(security/F-08): Normalize all auth failures to a single 401 response to avoid
        # token state enumeration (expired vs. invalid vs. missing are currently distinguishable).
        # Replace the branching below with a single: raise HTTPException(401, "Unauthorized")
        if _is_token_expired(token):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Token expirado",
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
        )
