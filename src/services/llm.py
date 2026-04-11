import asyncio
import logging
import time
from typing import Any

from openai import APIConnectionError, APIStatusError, APITimeoutError, AsyncOpenAI, RateLimitError

from src.config.settings import settings
from src.services import tracing

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

    with tracing.start_span("llm.call", {"llm.model": model}) as span:
        for attempt in range(1, max_retries + 1):
            try:
                t = time.perf_counter()
                response = await client.chat.completions.create(
                    model=model,
                    messages=messages,
                    **kwargs,
                )
                elapsed_ms = (time.perf_counter() - t) * 1000
                content = response.choices[0].message.content or ""
                if response.usage:
                    span.set_attribute("llm.tokens_in", response.usage.prompt_tokens)
                    span.set_attribute("llm.tokens_out", response.usage.completion_tokens)
                logger.info(
                    "LLM %-45s tokens_in=%-5s tokens_out=%-5s %.0fms",
                    model,
                    response.usage.prompt_tokens if response.usage else "?",
                    response.usage.completion_tokens if response.usage else "?",
                    elapsed_ms,
                )
                return content

            except APITimeoutError as e:
                logger.warning("LLM call timeout (attempt %d/%d)", attempt, max_retries)
                if attempt == max_retries:
                    span.record_exception(e)
                    span.set_status(tracing.STATUS_ERROR, "timeout")
                    raise LLMTimeoutError("LLM call timed out after all retries") from e
                await asyncio.sleep(delay)
                delay *= 2

            except RateLimitError as e:
                logger.warning("Rate limit hit (attempt %d/%d)", attempt, max_retries)
                if attempt == max_retries:
                    span.record_exception(e)
                    span.set_status(tracing.STATUS_ERROR, "rate_limit")
                    raise LLMRateLimitError("API rate limit reached after all retries") from e
                await asyncio.sleep(delay)
                delay *= 2

            except APIConnectionError as e:
                logger.warning("OpenRouter connection error (attempt %d/%d)", attempt, max_retries)
                if attempt == max_retries:
                    span.record_exception(e)
                    span.set_status(tracing.STATUS_ERROR, "connection_error")
                    raise
                await asyncio.sleep(delay)
                delay *= 2

            except APIStatusError as e:
                span.record_exception(e)
                span.set_status(tracing.STATUS_ERROR, str(e.status_code))
                logger.error("API status error: %s %s", e.status_code, e.message)
                raise

    raise RuntimeError("Failed after all attempts")
