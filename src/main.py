import ipaddress
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

# Telegram Bot API sends webhooks from these IP ranges
# https://core.telegram.org/bots/webhooks#the-short-version
TELEGRAM_IP_RANGES = [
    ipaddress.ip_network("149.154.160.0/20"),
    ipaddress.ip_network("91.108.4.0/22"),
]


def _is_telegram_ip(ip_str: str) -> bool:
    """Check if an IP address belongs to Telegram's known ranges."""
    try:
        addr = ipaddress.ip_address(ip_str)
        return any(addr in net for net in TELEGRAM_IP_RANGES)
    except ValueError:
        return False


@asynccontextmanager
async def lifespan(app: FastAPI):
    from src.scheduler.reports import start_scheduler, stop_scheduler
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(title="FinBot", docs_url=None, redoc_url=None, lifespan=lifespan)
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

    # 2. Validate source IP is from Telegram
    client_ip = request.headers.get("CF-Connecting-IP") or request.client.host
    if not _is_telegram_ip(client_ip):
        logger.warning("Webhook chamado de IP não-Telegram: %s", client_ip)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    update = await request.json()
    logger.debug("Update recebido: %s", update)

    # 3. Validate chat_id is authorized (single-user bot)
    chat_id = _extract_chat_id(update)
    if chat_id is not None and chat_id != settings.telegram_allowed_chat_id:
        logger.warning("Update ignorado de chat_id não autorizado: %d", chat_id)
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
