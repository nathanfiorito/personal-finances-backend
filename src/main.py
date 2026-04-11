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
from src.routers import categories, expenses, export, reports, transactions
from src.services.telegram import send_message

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ── SigNoz Observability (OpenTelemetry) ─────────────────────────────────────
# Configure OpenTelemetry before the app is created so all auto-instrumentation
# (httpx, supabase) is set up before the first request.
# FastAPI instrumentation will be applied after app creation.
if settings.signoz_otlp_endpoint:
    os.environ.setdefault("OTEL_SERVICE_NAME", settings.otel_service_name)
    try:
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.trace import TracerProvider, SpanProcessor
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry._logs import set_logger_provider
        from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
        from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
        from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter

        def _httpx_request_hook(span, request) -> None:
            """Rename generic httpx spans to include service + path for readability in SigNoz."""
            host = request.url.host
            path = request.url.path
            if "supabase.co" in host:
                prefix = "supabase"
            elif "openrouter.ai" in host:
                prefix = "openrouter"
            elif "api.telegram.org" in host:
                prefix = "telegram"
            else:
                prefix = host
            span.update_name(f"{prefix} {request.method} {path}")

        class _FilteringSpanProcessor(SpanProcessor):
            """Wraps a SpanProcessor and drops matching spans before export."""

            def __init__(self, inner: SpanProcessor, should_drop) -> None:
                self._inner = inner
                self._should_drop = should_drop

            def on_start(self, span, parent_context=None) -> None:
                pass  # BatchSpanProcessor.on_start is a no-op; skip to avoid overhead

            def on_end(self, span) -> None:
                if not self._should_drop(span):
                    self._inner.on_end(span)

            def shutdown(self) -> None:
                self._inner.shutdown()

            def force_flush(self, timeout_millis: int = 30000) -> bool:
                return self._inner.force_flush(timeout_millis)

        resource = Resource.create({"service.name": settings.otel_service_name})

        tracer_provider = TracerProvider(resource=resource)
        tracer_provider.add_span_processor(
            _FilteringSpanProcessor(
                BatchSpanProcessor(
                    OTLPSpanExporter(endpoint=f"{settings.signoz_otlp_endpoint}/v1/traces")
                ),
                # Drop ASGI response-chunk spans — they add noise without latency insight
                should_drop=lambda span: span.name.endswith(" http send"),
            )
        )
        trace.set_tracer_provider(tracer_provider)

        logger_provider = LoggerProvider(resource=resource)
        set_logger_provider(logger_provider)
        logger_provider.add_log_record_processor(
            BatchLogRecordProcessor(
                OTLPLogExporter(endpoint=f"{settings.signoz_otlp_endpoint}/v1/logs")
            )
        )
        logging.getLogger().addHandler(LoggingHandler(level=logging.INFO, logger_provider=logger_provider))

        HTTPXClientInstrumentor().instrument(request_hook=_httpx_request_hook)
        logger.info("SigNoz observability enabled (service=%s, endpoint=%s)", settings.otel_service_name, settings.signoz_otlp_endpoint)
    except ImportError as e:
        logger.warning("OpenTelemetry packages not installed — run: pip install -r requirements.txt (%s)", e)

limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])


@asynccontextmanager
async def lifespan(app: FastAPI):
    from src.scheduler.reports import start_scheduler, stop_scheduler
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(title="Personal Finances", docs_url=None, redoc_url=None, lifespan=lifespan)
# TODO(security/F-01): Disable OpenAPI schema in production to avoid exposing full API map to unauthenticated users.
# Add openapi_url=None to the FastAPI constructor above.
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Instrument FastAPI after app creation
if settings.signoz_otlp_endpoint:
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        FastAPIInstrumentor.instrument_app(app)
    except ImportError:
        pass

# CORS: allow requests from all subdomains of nathanfiorito.com.br
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https://([a-zA-Z0-9-]+\.)*nathanfiorito\.com\.br",
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
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


app.include_router(transactions.router)
app.include_router(expenses.router)  # 301 compat layer — keep until frontend is fully migrated
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
    logger.debug("Update received: %s", update)

    # 2. Validate chat_id is authorized (single-user bot)
    chat_id = _extract_chat_id(update)
    if chat_id is not None and chat_id != settings.telegram_allowed_chat_id:
        logger.warning("Webhook received from unauthorized chat_id: %d", chat_id)
        try:
            await send_message(chat_id, "Unsupported user")
        except Exception:
            logger.exception("Error sending unsupported user message to chat_id %d", chat_id)
        return {"ok": True}

    try:
        await handle_update(update)
    except Exception:
        logger.exception("Error processing update: %s", update)

    return {"ok": True}


def _extract_chat_id(update: dict) -> int | None:
    for key in ("message", "edited_message", "channel_post"):
        if key in update:
            return update[key].get("chat", {}).get("id")
    if "callback_query" in update:
        return update["callback_query"].get("message", {}).get("chat", {}).get("id")
    return None
