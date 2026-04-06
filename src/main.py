import logging

from fastapi import FastAPI, HTTPException, Request, status

from src.config.settings import settings
from src.handlers.message import handle_update

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="FinBot", docs_url=None, redoc_url=None)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/webhook")
async def webhook(request: Request) -> dict:
    # Validate Telegram secret token
    secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
    if secret != settings.telegram_webhook_secret:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    update = await request.json()
    logger.debug("Update recebido: %s", update)

    # Restrict to allowed chat_id
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
