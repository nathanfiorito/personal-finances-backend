import pytest
from unittest.mock import AsyncMock, MagicMock

import httpx

import src.services.llm as llm_module
from src.services.llm import LLMTimeoutError, LLMRateLimitError
from openai import APITimeoutError


def _make_timeout_error() -> APITimeoutError:
    return APITimeoutError(request=httpx.Request("POST", "https://openrouter.ai/api/v1/chat/completions"))


def _mock_response(content: str = "result", tokens_in: int = 10, tokens_out: int = 5) -> MagicMock:
    response = MagicMock()
    response.choices = [MagicMock(message=MagicMock(content=content))]
    response.usage = MagicMock(prompt_tokens=tokens_in, completion_tokens=tokens_out)
    return response


@pytest.fixture(autouse=True)
def reset_llm_client():
    original = llm_module._client
    llm_module._client = None
    yield
    llm_module._client = original


class TestChatCompletionSpans:
    @pytest.mark.asyncio
    async def test_creates_span_with_model_attribute(self, mocker):
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(return_value=_mock_response())
        mocker.patch("src.services.llm.get_client", return_value=mock_client)

        mock_span = MagicMock()
        mock_ctx = MagicMock()
        mock_ctx.__enter__.return_value = mock_span
        mock_ctx.__exit__.return_value = False
        mock_start_span = mocker.patch("src.services.llm.tracing.start_span", return_value=mock_ctx)

        await llm_module.chat_completion("anthropic/claude-haiku-4-5", [{"role": "user", "content": "hi"}])

        mock_start_span.assert_called_once_with("llm.call", {"llm.model": "anthropic/claude-haiku-4-5"})

    @pytest.mark.asyncio
    async def test_sets_token_attributes_after_response(self, mocker):
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(return_value=_mock_response(tokens_in=42, tokens_out=17))
        mocker.patch("src.services.llm.get_client", return_value=mock_client)

        mock_span = MagicMock()
        mock_ctx = MagicMock()
        mock_ctx.__enter__.return_value = mock_span
        mock_ctx.__exit__.return_value = False
        mocker.patch("src.services.llm.tracing.start_span", return_value=mock_ctx)

        await llm_module.chat_completion("anthropic/claude-haiku-4-5", [{"role": "user", "content": "hi"}])

        mock_span.set_attribute.assert_any_call("llm.tokens_in", 42)
        mock_span.set_attribute.assert_any_call("llm.tokens_out", 17)

    @pytest.mark.asyncio
    async def test_records_exception_on_final_timeout(self, mocker):
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(side_effect=_make_timeout_error())
        mocker.patch("src.services.llm.get_client", return_value=mock_client)
        mocker.patch("src.services.llm.asyncio.sleep", new_callable=AsyncMock)

        mock_span = MagicMock()
        mock_ctx = MagicMock()
        mock_ctx.__enter__.return_value = mock_span
        mock_ctx.__exit__.return_value = False
        mocker.patch("src.services.llm.tracing.start_span", return_value=mock_ctx)

        with pytest.raises(LLMTimeoutError):
            await llm_module.chat_completion("anthropic/claude-haiku-4-5", [{"role": "user", "content": "hi"}], max_retries=1)

        mock_span.record_exception.assert_called_once()
        mock_span.set_status.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_content_string(self, mocker):
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(return_value=_mock_response(content="hello world"))
        mocker.patch("src.services.llm.get_client", return_value=mock_client)

        mock_span = MagicMock()
        mock_ctx = MagicMock()
        mock_ctx.__enter__.return_value = mock_span
        mock_ctx.__exit__.return_value = False
        mocker.patch("src.services.llm.tracing.start_span", return_value=mock_ctx)

        result = await llm_module.chat_completion("anthropic/claude-haiku-4-5", [{"role": "user", "content": "hi"}])

        assert result == "hello world"

    @pytest.mark.asyncio
    async def test_no_error_on_span_when_retry_succeeds(self, mocker):
        """Span must not be marked as error when first attempt fails but second succeeds."""
        good_response = _mock_response(content="ok")
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(
            side_effect=[_make_timeout_error(), good_response]
        )
        mocker.patch("src.services.llm.get_client", return_value=mock_client)
        mocker.patch("src.services.llm.asyncio.sleep", new_callable=AsyncMock)

        mock_span = MagicMock()
        mock_ctx = MagicMock()
        mock_ctx.__enter__.return_value = mock_span
        mock_ctx.__exit__.return_value = False
        mocker.patch("src.services.llm.tracing.start_span", return_value=mock_ctx)

        result = await llm_module.chat_completion(
            "anthropic/claude-haiku-4-5",
            [{"role": "user", "content": "hi"}],
            max_retries=2,
        )

        assert result == "ok"
        mock_span.record_exception.assert_not_called()
        mock_span.set_status.assert_not_called()
