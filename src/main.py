import logging
import os
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from src.config.settings import settings
from src.handlers.message import handle_update
from src.routers import categories, expenses, export, reports
from src.services.telegram import send_message

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ── HyperDX Observability ────────────────────────────────────────────────────
# Configure OpenTelemetry before the app is created so all auto-instrumentation
# (httpx, fastapi, supabase) is set up before the first request.
if settings.hyperdx_api_key:
    os.environ.setdefault("HYPERDX_API_KEY", settings.hyperdx_api_key)
    os.environ.setdefault("OTEL_SERVICE_NAME", settings.otel_service_name)
    try:
        from hyperdx.opentelemetry import configure_opentelemetry
        configure_opentelemetry()
        logger.info("HyperDX observability enabled (service=%s)", settings.otel_service_name)
    except ImportError:
        logger.warning("hyperdx-opentelemetry not installed — run: pip install hyperdx-opentelemetry && opentelemetry-bootstrap -a install")

limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])


@asynccontextmanager
async def lifespan(app: FastAPI):
    from src.scheduler.reports import start_scheduler, stop_scheduler
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(title="FinBot", docs_url=None, redoc_url=None, lifespan=lifespan)
# TODO(security/F-01): Disable OpenAPI schema in production to avoid exposing full API map to unauthenticated users.
# Add openapi_url=None to the FastAPI constructor above.
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS: only allow requests from the frontend domain
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https://([a-zA-Z0-9-]+\.)*nathanfiorito\.com\.br",
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["*"],
    allow_credentials=False,
)


# TODO(security/F-04): Add security headers middleware below.
# response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
# response.headers["X-Content-Type-Options"] = "nosniff"
# response.headers["X-Frame-Options"] = "DENY"
# response.headers["Referrer-Policy"] = "no-referrer"


@app.middleware("http")
async def log_request_timing(request: Request, call_next):
    """Log every request with method, path, status code and total processing time."""
    start = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "→ %s %s %d (%.0fms)",
        request.method,
        request.url.path,
        response.status_code,
        elapsed_ms,
    )
    return response


app.include_router(expenses.router)
app.include_router(categories.router)
app.include_router(reports.router)
app.include_router(export.router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/webhook")
@limiter.limit("30/minute")
async def webhook(request: Request) -> dict:
    # 1. Validate Telegram secret token
    secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
    if secret != settings.telegram_webhook_secret:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    update = await request.json()
    logger.debug("Update recebido: %s", update)

    # 2. Validate chat_id is authorized (single-user bot)
    chat_id = _extract_chat_id(update)
    if chat_id is not None and chat_id != settings.telegram_allowed_chat_id:
        logger.warning("Webhook recebido de chat_id não autorizado: %d", chat_id)
        try:
            await send_message(chat_id, "Usuário não suportado")
        except Exception:
            logger.exception("Erro ao enviar mensagem de usuário não suportado para chat_id %d", chat_id)
        return {"ok": True}

    try:
        await handle_update(update)
    except Exception:
        logger.exception("Erro ao processar update: %s", update)

    return {"ok": True}


def _extract_chat_id(update: dict) -> int | None:
    for key in ("message", "edited_message", "channel_post"):
        if key in update:
            return update[key].get("chat", {}).get("id")
    if "callback_query" in update:
        return update["callback_query"].get("message", {}).get("chat", {}).get("id")
    return None
