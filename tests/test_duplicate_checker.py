import pytest
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import AsyncMock

from src.models.expense import Expense, ExtractedExpense
from src.agents.duplicate_checker import check_duplicate


def _expense(**kwargs) -> ExtractedExpense:
    defaults = dict(
        valor=Decimal("45.90"),
        data=date(2024, 1, 15),
        estabelecimento="Supermercado Extra",
        descricao="Compras do mês",
        tipo_entrada="texto",
        confianca=0.9,
    )
    defaults.update(kwargs)
    return ExtractedExpense(**defaults)


def _recent(valor="45.90", estabelecimento="Supermercado Extra") -> Expense:
    return Expense(
        id="uuid-1",
        valor=Decimal(valor),
        data=date(2024, 1, 14),
        estabelecimento=estabelecimento,
        descricao="Compras do mês",
        categoria="Alimentação",
        cnpj=None,
        tipo_entrada="texto",
        confianca=0.9,
        created_at=datetime(2024, 1, 14, 10, 0, 0),
    )


class TestCheckDuplicate:
    @pytest.mark.asyncio
    async def test_empty_recent_returns_none(self):
        result = await check_duplicate(_expense(), [])
        assert result is None

    @pytest.mark.asyncio
    async def test_duplicate_detected_returns_reason(self, mocker):
        mocker.patch(
            "src.agents.duplicate_checker.chat_completion",
            new_callable=AsyncMock,
            return_value="DUPLICATA: Mesmo valor e estabelecimento registrados ontem",
        )
        result = await check_duplicate(_expense(), [_recent()])
        assert result is not None
        assert "estabelecimento" in result.lower() or len(result) > 0

    @pytest.mark.asyncio
    async def test_no_duplicate_returns_none(self, mocker):
        mocker.patch(
            "src.agents.duplicate_checker.chat_completion",
            new_callable=AsyncMock,
            return_value="OK",
        )
        result = await check_duplicate(_expense(), [_recent(valor="200.00")])
        assert result is None

    @pytest.mark.asyncio
    async def test_llm_failure_returns_none(self, mocker):
        mocker.patch(
            "src.agents.duplicate_checker.chat_completion",
            new_callable=AsyncMock,
            side_effect=Exception("LLM timeout"),
        )
        result = await check_duplicate(_expense(), [_recent()])
        assert result is None

    @pytest.mark.asyncio
    async def test_uses_model_fast(self, mocker):
        from src.config.settings import settings
        mock_llm = mocker.patch(
            "src.agents.duplicate_checker.chat_completion",
            new_callable=AsyncMock,
            return_value="OK",
        )
        await check_duplicate(_expense(), [_recent()])
        called_model = mock_llm.call_args.kwargs.get("model") or mock_llm.call_args.args[0]
        assert called_model == settings.model_fast

    @pytest.mark.asyncio
    async def test_case_insensitive_ok_response(self, mocker):
        mocker.patch(
            "src.agents.duplicate_checker.chat_completion",
            new_callable=AsyncMock,
            return_value="ok",
        )
        result = await check_duplicate(_expense(), [_recent()])
        assert result is None
