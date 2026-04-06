import pytest
from decimal import Decimal
from datetime import date
from unittest.mock import AsyncMock, patch

from src.agents.extractor import (
    ExtractionError,
    _parse_llm_json,
    _build_expense,
    extract_from_image,
    extract_from_text,
)
from src.services.llm import LLMTimeoutError, LLMRateLimitError


class TestParseLlmJson:
    def test_clean_json(self):
        raw = '{"valor": 45.90, "data": "2024-01-15", "estabelecimento": "Mercado", "descricao": null, "cnpj": null, "confianca": 0.9}'
        result = _parse_llm_json(raw)
        assert result["valor"] == 45.90

    def test_json_wrapped_in_markdown(self):
        raw = '```json\n{"valor": 10.0}\n```'
        result = _parse_llm_json(raw)
        assert result["valor"] == 10.0

    def test_json_with_surrounding_text(self):
        raw = 'Aqui está o JSON:\n{"valor": 99.99}\nEspero que ajude!'
        result = _parse_llm_json(raw)
        assert result["valor"] == 99.99

    def test_invalid_json_raises(self):
        with pytest.raises(ExtractionError):
            _parse_llm_json("isso não é json")


class TestBuildExpense:
    def _base(self, **overrides) -> dict:
        data = {
            "valor": 50.0,
            "data": "2024-03-10",
            "estabelecimento": "Posto Shell",
            "descricao": "Combustível",
            "cnpj": None,
            "confianca": 0.95,
        }
        data.update(overrides)
        return data

    def test_basic_build(self):
        expense = _build_expense(self._base(), "texto")
        assert expense.valor == Decimal("50.0")
        assert expense.data == date(2024, 3, 10)
        assert expense.estabelecimento == "Posto Shell"
        assert expense.confianca == 0.95
        assert expense.tipo_entrada == "texto"

    def test_missing_valor_raises(self):
        with pytest.raises(ExtractionError, match="valor"):
            _build_expense({"data": "2024-01-01", "confianca": 0.5}, "texto")

    def test_invalid_data_falls_back_to_today(self):
        expense = _build_expense(self._base(data="not-a-date"), "imagem")
        assert expense.data == date.today()

    def test_null_data_falls_back_to_today(self):
        expense = _build_expense(self._base(data=None), "imagem")
        assert expense.data == date.today()

    def test_cnpj_formatted(self):
        expense = _build_expense(self._base(cnpj="12345678000195"), "imagem")
        assert expense.cnpj == "12.345.678/0001-95"

    def test_empty_string_fields_become_none(self):
        expense = _build_expense(self._base(estabelecimento="", descricao=""), "texto")
        assert expense.estabelecimento is None
        assert expense.descricao is None


class TestExtractFromText:
    @pytest.mark.asyncio
    async def test_successful_extraction(self):
        mock_response = '{"valor": 120.0, "data": null, "estabelecimento": "Posto Shell", "descricao": "Combustível", "cnpj": null, "confianca": 0.85}'

        with patch("src.agents.extractor.llm.chat_completion", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = mock_response
            expense = await extract_from_text("gastei 120 no posto shell")

        assert expense.valor == Decimal("120.0")
        assert expense.estabelecimento == "Posto Shell"
        assert expense.tipo_entrada == "texto"
        mock_llm.assert_called_once()

    @pytest.mark.asyncio
    async def test_invalid_json_raises_extraction_error(self):
        with patch("src.agents.extractor.llm.chat_completion", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = "desculpe, não entendi"

            with pytest.raises(ExtractionError):
                await extract_from_text("xyzabc")

    @pytest.mark.asyncio
    async def test_uses_fast_model(self):
        mock_response = '{"valor": 50.0, "data": "2024-01-01", "estabelecimento": "Mercado", "descricao": null, "cnpj": null, "confianca": 0.9}'

        with patch("src.agents.extractor.llm.chat_completion", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = mock_response
            await extract_from_text("50 no mercado")

        call_kwargs = mock_llm.call_args
        assert "haiku" in call_kwargs.kwargs.get("model", call_kwargs.args[0] if call_kwargs.args else "")


class TestExtractFromImage:
    @pytest.mark.asyncio
    async def test_successful_extraction(self):
        mock_response = '{"valor": 45.90, "data": "2024-01-15", "estabelecimento": "Supermercado Extra", "descricao": "Compras", "cnpj": "12.345.678/0001-95", "confianca": 0.92}'
        fake_image = b"\xff\xd8\xff" + b"\x00" * 100  # minimal fake JPEG header

        with patch("src.agents.extractor.llm.chat_completion", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = mock_response
            expense = await extract_from_image(fake_image)

        assert expense.valor == Decimal("45.90")
        assert expense.estabelecimento == "Supermercado Extra"
        assert expense.tipo_entrada == "imagem"
        assert expense.cnpj == "12.345.678/0001-95"

    @pytest.mark.asyncio
    async def test_uses_vision_model(self):
        mock_response = '{"valor": 10.0, "data": "2024-01-01", "estabelecimento": null, "descricao": null, "cnpj": null, "confianca": 0.5}'
        fake_image = b"\xff\xd8\xff" + b"\x00" * 100

        with patch("src.agents.extractor.llm.chat_completion", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = mock_response
            await extract_from_image(fake_image)

        call_kwargs = mock_llm.call_args
        model_arg = call_kwargs.kwargs.get("model", call_kwargs.args[0] if call_kwargs.args else "")
        assert "sonnet" in model_arg


class TestLLMErrors:
    @pytest.mark.asyncio
    async def test_timeout_propagates_from_text(self):
        with patch("src.agents.extractor.llm.chat_completion", new_callable=AsyncMock) as mock_llm:
            mock_llm.side_effect = LLMTimeoutError("timeout")
            with pytest.raises(LLMTimeoutError):
                await extract_from_text("gastei 50")

    @pytest.mark.asyncio
    async def test_rate_limit_propagates_from_text(self):
        with patch("src.agents.extractor.llm.chat_completion", new_callable=AsyncMock) as mock_llm:
            mock_llm.side_effect = LLMRateLimitError("rate limit")
            with pytest.raises(LLMRateLimitError):
                await extract_from_text("gastei 50")

    @pytest.mark.asyncio
    async def test_timeout_propagates_from_image(self):
        fake_image = b"\xff\xd8\xff" + b"\x00" * 100
        with patch("src.agents.extractor.llm.chat_completion", new_callable=AsyncMock) as mock_llm:
            mock_llm.side_effect = LLMTimeoutError("timeout")
            with pytest.raises(LLMTimeoutError):
                await extract_from_image(fake_image)


class TestExpenseModel:
    def test_valor_negativo_raises(self):
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            from src.models.expense import ExtractedExpense
            ExtractedExpense(valor=Decimal("-10"), data=date.today(), tipo_entrada="texto")

    def test_valor_acima_do_limite_raises(self):
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            from src.models.expense import ExtractedExpense
            ExtractedExpense(valor=Decimal("1000000"), data=date.today(), tipo_entrada="texto")
