import logging
import time

from src.config.settings import settings
from src.models.expense import ExtractedExpense
from src.services import llm

logger = logging.getLogger(__name__)

CATEGORIES = [
    "Alimentação",
    "Transporte",
    "Moradia",
    "Saúde",
    "Educação",
    "Lazer",
    "Vestuário",
    "Serviços",
    "Pets",
    "Outros",
]

_PROMPT = """Classifique a despesa abaixo em UMA das categorias: {categories}

Estabelecimento: {estabelecimento}
Descrição: {descricao}

Exemplos:
- Supermercado, Mercado, iFood, Rappi, McDonald's, restaurante, padaria → Alimentação
- Uber, Shell, Posto, estacionamento, pedágio, ônibus, metrô → Transporte
- Aluguel, condomínio, energia, água, gás, internet → Moradia
- Farmácia, Drogasil, hospital, clínica, plano de saúde → Saúde
- Curso, livro, Udemy, escola → Educação
- Cinema, Netflix, Spotify, viagem, show → Lazer
- Loja de roupas, calçados, acessórios → Vestuário
- Banco, cartório, seguro, manutenção → Serviços
- Pet shop, veterinário, ração → Pets

Responda APENAS com o nome exato da categoria, sem explicação."""

_CACHE_TTL = 300  # 5 minutes
_categories_cache: list[str] | None = None
_cache_expires_at: float = 0.0


async def _get_categories() -> list[str]:
    global _categories_cache, _cache_expires_at
    if _categories_cache is not None and time.monotonic() < _cache_expires_at:
        return _categories_cache
    try:
        from src.services import database
        cats = await database.get_active_categories()
        if cats:
            _categories_cache = cats
            _cache_expires_at = time.monotonic() + _CACHE_TTL
            return _categories_cache
    except Exception:
        logger.warning("Falha ao buscar categorias do banco — usando lista padrão")
    return CATEGORIES


async def categorize(expense: ExtractedExpense) -> str:
    categories = await _get_categories()
    estabelecimento = expense.estabelecimento or "Não informado"
    descricao = expense.descricao or "Não informada"

    prompt = _PROMPT.format(
        categories=", ".join(categories),
        estabelecimento=estabelecimento,
        descricao=descricao,
    )

    try:
        raw = await llm.chat_completion(
            model=settings.model_fast,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=20,
        )
        categoria = raw.strip().rstrip(".")

        if categoria in categories:
            logger.info("Categoria: %r (estabelecimento=%r)", categoria, expense.estabelecimento)
            return categoria

        for cat in categories:
            if cat.lower() == categoria.lower():
                return cat

        logger.warning("Categoria inválida retornada pelo LLM: %r — usando Outros", categoria)
        return "Outros"

    except Exception:
        logger.exception("Falha na categorização — usando Outros")
        return "Outros"
