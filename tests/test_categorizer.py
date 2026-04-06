import pytest
from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, patch

from src.agents.categorizer import categorize, CATEGORIES
from src.models.expense import ExtractedExpense


def _expense(estabelecimento: str | None = None, descricao: str | None = None) -> ExtractedExpense:
    return ExtractedExpense(
        valor=Decimal("50.00"),
        data=date.today(),
        estabelecimento=estabelecimento,
        descricao=descricao,
        tipo_entrada="texto",
    )


class TestCategorize:
    @pytest.mark.asyncio
    async def test_alimentacao(self):
        with patch("src.agents.categorizer.llm.chat_completion", new_callable=AsyncMock) as mock:
            mock.return_value = "Alimentação"
            result = await categorize(_expense("Supermercado Extra"))
        assert result == "Alimentação"

    @pytest.mark.asyncio
    async def test_transporte(self):
        with patch("src.agents.categorizer.llm.chat_completion", new_callable=AsyncMock) as mock:
            mock.return_value = "Transporte"
            result = await categorize(_expense("Uber"))
        assert result == "Transporte"

    @pytest.mark.asyncio
    async def test_invalid_category_falls_back_to_outros(self):
        with patch("src.agents.categorizer.llm.chat_completion", new_callable=AsyncMock) as mock:
            mock.return_value = "Categoria Inexistente"
            result = await categorize(_expense("Loja Desconhecida"))
        assert result == "Outros"

    @pytest.mark.asyncio
    async def test_case_insensitive_match(self):
        with patch("src.agents.categorizer.llm.chat_completion", new_callable=AsyncMock) as mock:
            mock.return_value = "saúde"
            result = await categorize(_expense("Drogasil"))
        assert result == "Saúde"

    @pytest.mark.asyncio
    async def test_llm_failure_falls_back_to_outros(self):
        with patch("src.agents.categorizer.llm.chat_completion", new_callable=AsyncMock) as mock:
            mock.side_effect = Exception("API error")
            result = await categorize(_expense("Qualquer coisa"))
        assert result == "Outros"

    @pytest.mark.asyncio
    async def test_trailing_period_stripped(self):
        with patch("src.agents.categorizer.llm.chat_completion", new_callable=AsyncMock) as mock:
            mock.return_value = "Lazer."
            result = await categorize(_expense("Netflix"))
        assert result == "Lazer"

    @pytest.mark.asyncio
    async def test_uses_fast_model(self):
        with patch("src.agents.categorizer.llm.chat_completion", new_callable=AsyncMock) as mock:
            mock.return_value = "Outros"
            await categorize(_expense("Teste"))
        model_arg = mock.call_args.kwargs.get("model", "")
        assert "haiku" in model_arg

    def test_all_categories_defined(self):
        assert len(CATEGORIES) == 10
        assert "Outros" in CATEGORIES
