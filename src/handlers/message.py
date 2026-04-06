import logging

from src.agents import extractor, categorizer
from src.agents.extractor import ExtractionError
from src.handlers.commands import dispatch_command
from src.models import pending as pending_store
from src.models.expense import ExtractedExpense
from src.services import telegram
from src.services.llm import LLMRateLimitError, LLMTimeoutError

logger = logging.getLogger(__name__)


def _get_largest_photo_file_id(photos: list[dict]) -> str:
    return max(photos, key=lambda p: p["file_size"])["file_id"]


def _format_extracted(expense: ExtractedExpense, categoria: str) -> str:
    data_fmt = expense.data.strftime("%d/%m/%Y")
    valor_fmt = f"R$ {expense.valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    confianca_pct = int(expense.confianca * 100)

    lines = [
        "📋 <b>Despesa detectada:</b>",
        f"💰 Valor: <b>{valor_fmt}</b>",
        f"📅 Data: {data_fmt}",
    ]
    if expense.estabelecimento:
        lines.append(f"🏪 Estabelecimento: {expense.estabelecimento}")
    if expense.descricao:
        lines.append(f"📝 Descrição: {expense.descricao}")
    if expense.cnpj:
        lines.append(f"🔢 CNPJ: {expense.cnpj}")
    lines.append(f"🏷️ Categoria: <b>{categoria}</b>")
    lines.append(f"\n🎯 Confiança: {confianca_pct}%")
    return "\n".join(lines)


async def _send_confirmation(chat_id: int, expense: ExtractedExpense, categoria: str) -> None:
    msg = await telegram.send_message(
        chat_id,
        _format_extracted(expense, categoria),
        reply_markup=telegram._confirmation_keyboard(),
    )
    message_id = msg["result"]["message_id"]
    pending_store.save(chat_id, expense, categoria, message_id)


async def handle_update(update: dict) -> None:
    message = update.get("message") or update.get("edited_message")
    callback_query = update.get("callback_query")

    if callback_query:
        from src.handlers.callback import handle_callback
        await handle_callback(callback_query)
        return

    if not message:
        return

    chat_id: int = message["chat"]["id"]

    if message.get("photo"):
        await handle_photo(chat_id, message)
    elif message.get("document"):
        doc = message["document"]
        if doc.get("mime_type") == "application/pdf":
            await handle_pdf(chat_id, doc)
        else:
            await telegram.send_message(chat_id, "Por favor, envie uma imagem ou PDF.")
    elif message.get("text"):
        text: str = message["text"]
        if text.startswith("/"):
            await dispatch_command(chat_id, text)
        else:
            await handle_text(chat_id, text)
    else:
        await telegram.send_message(
            chat_id, "Formato não suportado. Envie uma foto, PDF ou texto."
        )


async def handle_photo(chat_id: int, message: dict) -> None:
    await telegram.send_message(chat_id, "⏳ Analisando comprovante...")
    file_id = _get_largest_photo_file_id(message["photo"])

    try:
        image_bytes = await telegram.get_file(file_id)
        expense = await extractor.extract_from_image(image_bytes)
        categoria = await categorizer.categorize(expense)
        await _send_confirmation(chat_id, expense, categoria)
    except LLMTimeoutError:
        await telegram.send_message(chat_id, "⏱️ O serviço de IA demorou demais. Tente novamente.")
    except LLMRateLimitError:
        await telegram.send_message(chat_id, "⚠️ Muitas requisições. Aguarde alguns segundos e tente novamente.")
    except ExtractionError as e:
        logger.warning("Falha na extração de imagem: %s", e)
        await telegram.send_message(
            chat_id,
            "⚠️ Não consegui extrair os dados deste comprovante. "
            "Tente enviar uma foto mais nítida ou descreva a despesa em texto.",
        )
    except Exception:
        logger.exception("Erro inesperado ao processar imagem")
        await telegram.send_message(chat_id, "❌ Ocorreu um erro inesperado. Tente novamente.")


async def handle_text(chat_id: int, text: str) -> None:
    await telegram.send_message(chat_id, "⏳ Processando...")

    try:
        expense = await extractor.extract_from_text(text)
        categoria = await categorizer.categorize(expense)
        await _send_confirmation(chat_id, expense, categoria)
    except LLMTimeoutError:
        await telegram.send_message(chat_id, "⏱️ O serviço de IA demorou demais. Tente novamente.")
    except LLMRateLimitError:
        await telegram.send_message(chat_id, "⚠️ Muitas requisições. Aguarde alguns segundos e tente novamente.")
    except ExtractionError as e:
        logger.warning("Falha na extração de texto: %s", e)
        await telegram.send_message(
            chat_id,
            "⚠️ Não entendi a despesa. Tente algo como: <i>\"gastei 50 reais no mercado\"</i>",
        )
    except Exception:
        logger.exception("Erro inesperado ao processar texto")
        await telegram.send_message(chat_id, "❌ Ocorreu um erro inesperado. Tente novamente.")


async def handle_pdf(chat_id: int, document: dict) -> None:
    if document.get("file_size", 0) > 10 * 1024 * 1024:
        await telegram.send_message(
            chat_id, "⚠️ PDF muito grande (máx. 10MB). Tente tirar uma foto do documento."
        )
        return

    await telegram.send_message(chat_id, "⏳ Processando PDF...")

    try:
        pdf_bytes = await telegram.get_file(document["file_id"])
        expense = await extractor.extract_from_pdf(pdf_bytes)
        categoria = await categorizer.categorize(expense)
        await _send_confirmation(chat_id, expense, categoria)
    except LLMTimeoutError:
        await telegram.send_message(chat_id, "⏱️ O serviço de IA demorou demais. Tente novamente.")
    except LLMRateLimitError:
        await telegram.send_message(chat_id, "⚠️ Muitas requisições. Aguarde alguns segundos e tente novamente.")
    except ExtractionError as e:
        logger.warning("Falha na extração de PDF: %s", e)
        await telegram.send_message(
            chat_id,
            "⚠️ Não consegui extrair os dados deste PDF. Tente tirar uma foto do documento.",
        )
    except Exception:
        logger.exception("Erro inesperado ao processar PDF")
        await telegram.send_message(chat_id, "❌ Ocorreu um erro inesperado. Tente novamente.")
