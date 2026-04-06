import asyncio
import logging
from typing import Any

from openai import AsyncOpenAI, APIConnectionError, APIStatusError, APITimeoutError, RateLimitError

from src.config.settings import settings

logger = logging.getLogger(__name__)

_client: AsyncOpenAI | None = None


class LLMTimeoutError(Exception):
    pass


class LLMRateLimitError(Exception):
    pass


def get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(
            api_key=settings.openrouter_api_key,
            base_url=settings.openrouter_base_url,
            timeout=30.0,
        )
    return _client


async def chat_completion(
    model: str,
    messages: list[dict],
    max_retries: int = 3,
    **kwargs: Any,
) -> str:
    client = get_client()
    delay = 1.0

    for attempt in range(1, max_retries + 1):
        try:
            response = await client.chat.completions.create(
                model=model,
                messages=messages,
                **kwargs,
            )
            content = response.choices[0].message.content or ""
            logger.info(
                "LLM call: model=%s tokens_in=%s tokens_out=%s",
                model,
                response.usage.prompt_tokens if response.usage else "?",
                response.usage.completion_tokens if response.usage else "?",
            )
            return content

        except APITimeoutError as e:
            logger.warning("Timeout na chamada ao LLM (tentativa %d/%d)", attempt, max_retries)
            if attempt == max_retries:
                raise LLMTimeoutError("Tempo limite excedido ao chamar o LLM") from e
            await asyncio.sleep(delay)
            delay *= 2

        except RateLimitError as e:
            logger.warning("Rate limit atingido (tentativa %d/%d)", attempt, max_retries)
            if attempt == max_retries:
                raise LLMRateLimitError("Limite de requisições da API atingido") from e
            await asyncio.sleep(delay)
            delay *= 2

        except APIConnectionError:
            logger.warning("Erro de conexão com OpenRouter (tentativa %d/%d)", attempt, max_retries)
            if attempt == max_retries:
                raise
            await asyncio.sleep(delay)
            delay *= 2

        except APIStatusError as e:
            logger.error("Erro de status da API: %s %s", e.status_code, e.message)
            raise

    raise RuntimeError("Falha após todas as tentativas")
