import pytest
from decimal import Decimal
from datetime import date
from unittest.mock import AsyncMock, patch

from src.agents.extractor import (
    ExtractionError,
    _parse_llm_json,
    _build_expense,
    _extract_text_from_pdf,
    extract_from_image,
    extract_from_text,
    extract_from_pdf,
)
from src.services.llm import LLMTimeoutError, LLMRateLimitError


class TestParseLlmJson:
    def test_clean_json(self):
        raw = '{"amount": 45.90, "date": "2024-01-15", "establishment": "Mercado", "description": null, "tax_id": null, "confidence": 0.9}'
        result = _parse_llm_json(raw)
        assert result["amount"] == 45.90

    def test_json_wrapped_in_markdown(self):
        raw = '```json\n{"amount": 10.0}\n```'
        result = _parse_llm_json(raw)
        assert result["amount"] == 10.0

    def test_json_with_surrounding_text(self):
        raw = 'Aqui está o JSON:\n{"amount": 99.99}\nEspero que ajude!'
        result = _parse_llm_json(raw)
        assert result["amount"] == 99.99

    def test_invalid_json_raises(self):
        with pytest.raises(ExtractionError):
            _parse_llm_json("isso não é json")


class TestBuildExpense:
    def _base(self, **overrides) -> dict:
        data = {
            "amount": 50.0,
            "date": "2024-03-10",
            "establishment": "Posto Shell",
            "description": "Combustível",
            "tax_id": None,
            "confidence": 0.95,
        }
        data.update(overrides)
        return data

    def test_basic_build(self):
        expense = _build_expense(self._base(), "texto")
        assert expense.amount == Decimal("50.0")
        assert expense.date == date(2024, 3, 10)
        assert expense.establishment == "Posto Shell"
        assert expense.confidence == 0.95
        assert expense.entry_type == "texto"

    def test_missing_amount_raises(self):
        with pytest.raises(ExtractionError, match="amount"):
            _build_expense({"date": "2024-01-01", "confidence": 0.5}, "texto")

    def test_invalid_date_falls_back_to_today(self):
        expense = _build_expense(self._base(date="not-a-date"), "imagem")
        assert expense.date == date.today()

    def test_null_date_falls_back_to_today(self):
        expense = _build_expense(self._base(date=None), "imagem")
        assert expense.date == date.today()

    def test_tax_id_formatted(self):
        expense = _build_expense(self._base(tax_id="12345678000195"), "imagem")
        assert expense.tax_id == "12.345.678/0001-95"

    def test_empty_string_fields_become_none(self):
        expense = _build_expense(self._base(establishment="", description=""), "texto")
        assert expense.establishment is None
        assert expense.description is None


class TestExtractFromText:
    @pytest.mark.asyncio
    async def test_successful_extraction(self):
        mock_response = '{"amount": 120.0, "date": null, "establishment": "Posto Shell", "description": "Combustível", "tax_id": null, "confidence": 0.85}'

        with patch("src.agents.extractor.llm.chat_completion", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = mock_response
            expense = await extract_from_text("gastei 120 no posto shell")

        assert expense.amount == Decimal("120.0")
        assert expense.establishment == "Posto Shell"
        assert expense.entry_type == "texto"
        mock_llm.assert_called_once()

    @pytest.mark.asyncio
    async def test_invalid_json_raises_extraction_error(self):
        with patch("src.agents.extractor.llm.chat_completion", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = "desculpe, não entendi"

            with pytest.raises(ExtractionError):
                await extract_from_text("xyzabc")

    @pytest.mark.asyncio
    async def test_uses_fast_model(self):
        mock_response = '{"amount": 50.0, "date": "2024-01-01", "establishment": "Mercado", "description": null, "tax_id": null, "confidence": 0.9}'

        with patch("src.agents.extractor.llm.chat_completion", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = mock_response
            await extract_from_text("50 no mercado")

        call_kwargs = mock_llm.call_args
        assert "haiku" in call_kwargs.kwargs.get("model", call_kwargs.args[0] if call_kwargs.args else "")


class TestExtractFromImage:
    @pytest.mark.asyncio
    async def test_successful_extraction(self):
        mock_response = '{"amount": 45.90, "date": "2024-01-15", "establishment": "Supermercado Extra", "description": "Compras", "tax_id": "12.345.678/0001-95", "confidence": 0.92}'
        fake_image = b"\xff\xd8\xff" + b"\x00" * 100  # minimal fake JPEG header

        with patch("src.agents.extractor.llm.chat_completion", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = mock_response
            expense = await extract_from_image(fake_image)

        assert expense.amount == Decimal("45.90")
        assert expense.establishment == "Supermercado Extra"
        assert expense.entry_type == "imagem"
        assert expense.tax_id == "12.345.678/0001-95"

    @pytest.mark.asyncio
    async def test_uses_vision_model(self):
        mock_response = '{"amount": 10.0, "date": "2024-01-01", "establishment": null, "description": null, "tax_id": null, "confidence": 0.5}'
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


class TestExtractFromPdf:
    @pytest.mark.asyncio
    async def test_pdf_with_text_uses_haiku(self, mocker):
        mocker.patch("src.agents.extractor._extract_text_from_pdf", return_value="NF-e valor R$ 150,00 data 2024-01-15")
        mock_llm = mocker.patch("src.agents.extractor.llm.chat_completion", new_callable=AsyncMock)
        mock_llm.return_value = '{"amount": 150.0, "date": "2024-01-15", "establishment": "Loja X", "description": null, "tax_id": null, "confidence": 0.95}'

        expense = await extract_from_pdf(b"fake-pdf")

        assert expense.entry_type == "pdf"
        assert expense.amount == Decimal("150.0")
        model_arg = mock_llm.call_args.kwargs.get("model", mock_llm.call_args.args[0] if mock_llm.call_args.args else "")
        assert "haiku" in model_arg

    @pytest.mark.asyncio
    async def test_pdf_without_text_falls_back_to_vision(self, mocker):
        mocker.patch("src.agents.extractor._extract_text_from_pdf", return_value=None)
        mocker.patch("src.agents.extractor._pdf_to_image", return_value=b"\xff\xd8\xff" + b"\x00" * 100)
        mock_llm = mocker.patch("src.agents.extractor.llm.chat_completion", new_callable=AsyncMock)
        mock_llm.return_value = '{"amount": 80.0, "date": "2024-01-15", "establishment": null, "description": null, "tax_id": null, "confidence": 0.7}'

        expense = await extract_from_pdf(b"fake-scanned-pdf")

        assert expense.entry_type == "pdf"
        model_arg = mock_llm.call_args.kwargs.get("model", mock_llm.call_args.args[0] if mock_llm.call_args.args else "")
        assert "sonnet" in model_arg

    def test_extract_text_returns_none_for_short_text(self, mocker):
        import io
        mock_pdf = mocker.MagicMock()
        mock_pdf.__enter__ = mocker.MagicMock(return_value=mock_pdf)
        mock_pdf.__exit__ = mocker.MagicMock(return_value=False)
        mock_pdf.pages = [mocker.MagicMock(extract_text=mocker.MagicMock(return_value="abc"))]
        mocker.patch("pdfplumber.open", return_value=mock_pdf)

        result = _extract_text_from_pdf(b"fake")
        assert result is None  # "abc" < 50 chars

    def test_extract_text_returns_none_on_exception(self, mocker):
        mocker.patch("pdfplumber.open", side_effect=Exception("corrupt pdf"))
        result = _extract_text_from_pdf(b"corrupt")
        assert result is None


class TestBuildExpenseTransactionType:
    """Tests for transaction_type detection in _build_expense."""

    def _base(self, **overrides) -> dict:
        data = {
            "amount": 50.0,
            "date": "2024-03-10",
            "establishment": "Loja X",
            "description": None,
            "tax_id": None,
            "confidence": 0.9,
        }
        data.update(overrides)
        return data

    def test_outcome_is_preserved(self):
        # Arrange + Act
        expense = _build_expense(self._base(transaction_type="outcome"), "texto")
        # Assert
        assert expense.transaction_type == "outcome"

    def test_income_is_preserved(self):
        # Arrange + Act
        expense = _build_expense(self._base(transaction_type="income"), "texto")
        # Assert
        assert expense.transaction_type == "income"

    def test_missing_transaction_type_defaults_to_outcome(self):
        # Arrange: LLM did not return the field
        expense = _build_expense(self._base(), "texto")
        # Assert
        assert expense.transaction_type == "outcome"

    def test_invalid_transaction_type_defaults_to_outcome(self):
        # Arrange: LLM returned an unexpected value
        expense = _build_expense(self._base(transaction_type="expense"), "texto")
        # Assert
        assert expense.transaction_type == "outcome"

    def test_none_transaction_type_defaults_to_outcome(self):
        # Arrange: LLM returned null
        expense = _build_expense(self._base(transaction_type=None), "texto")
        # Assert
        assert expense.transaction_type == "outcome"


class TestExtractFromTextTransactionType:
    """End-to-end transaction_type extraction via extract_from_text."""

    @pytest.mark.asyncio
    async def test_income_message_returns_income_type(self):
        # Arrange: LLM identifies the message as income
        mock_response = (
            '{"amount": 3000.0, "date": "2025-03-05", "establishment": null, '
            '"description": "Salário", "tax_id": null, "transaction_type": "income", "confidence": 0.95}'
        )
        with patch("src.agents.extractor.llm.chat_completion", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = mock_response
            # Act
            expense = await extract_from_text("recebi 3000 de salário")
        # Assert
        assert expense.transaction_type == "income"

    @pytest.mark.asyncio
    async def test_outcome_message_returns_outcome_type(self):
        # Arrange: LLM identifies the message as outcome
        mock_response = (
            '{"amount": 50.0, "date": "2025-03-10", "establishment": "Mercado", '
            '"description": null, "tax_id": null, "transaction_type": "outcome", "confidence": 0.9}'
        )
        with patch("src.agents.extractor.llm.chat_completion", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = mock_response
            # Act
            expense = await extract_from_text("gastei 50 no mercado")
        # Assert
        assert expense.transaction_type == "outcome"

    @pytest.mark.asyncio
    async def test_ambiguous_message_defaults_to_outcome(self):
        # Arrange: LLM does not include transaction_type
        mock_response = (
            '{"amount": 100.0, "date": null, "establishment": null, '
            '"description": "transação", "tax_id": null, "confidence": 0.5}'
        )
        with patch("src.agents.extractor.llm.chat_completion", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = mock_response
            # Act
            expense = await extract_from_text("100 reais")
        # Assert
        assert expense.transaction_type == "outcome"


class TestExpenseModel:
    def test_amount_negative_raises(self):
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            from src.models.expense import ExtractedExpense
            ExtractedExpense(amount=Decimal("-10"), date=date.today(), entry_type="texto")

    def test_amount_above_limit_raises(self):
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            from src.models.expense import ExtractedExpense
            ExtractedExpense(amount=Decimal("1000000"), date=date.today(), entry_type="texto")

    def test_transaction_type_defaults_to_outcome(self):
        # Arrange + Act
        from src.models.expense import ExtractedExpense
        expense = ExtractedExpense(amount=Decimal("50"), date=date.today(), entry_type="texto")
        # Assert
        assert expense.transaction_type == "outcome"

    def test_transaction_type_income_accepted(self):
        # Arrange + Act
        from src.models.expense import ExtractedExpense
        expense = ExtractedExpense(
            amount=Decimal("1000"),
            date=date.today(),
            entry_type="texto",
            transaction_type="income",
        )
        # Assert
        assert expense.transaction_type == "income"
