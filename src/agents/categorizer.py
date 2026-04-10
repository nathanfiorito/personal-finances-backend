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

_PROMPT = """Classify the expense below into ONE of the categories: {categories}

Establishment: {establishment}
Description: {description}

Examples:
- Supermarket, Market, iFood, Rappi, McDonald's, restaurant, bakery → Alimentação
- Uber, Shell, Gas station, parking, toll, bus, subway → Transporte
- Rent, condo, electricity, water, gas, internet → Moradia
- Pharmacy, hospital, clinic, health insurance → Saúde
- Course, book, Udemy, school → Educação
- Cinema, Netflix, Spotify, travel, show → Lazer
- Clothing store, shoes, accessories → Vestuário
- Bank, notary, insurance, maintenance → Serviços
- Pet shop, veterinarian, pet food → Pets

Respond ONLY with the exact category name, no explanation."""

_CACHE_TTL = 300  # 5 minutes
_categories_cache: list[str] | None = None
_cache_expires_at: float = 0.0


def invalidate_cache() -> None:
    global _categories_cache, _cache_expires_at
    _categories_cache = None
    _cache_expires_at = 0.0


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
        logger.warning("Failed to fetch categories from DB — using default list")
    return CATEGORIES


async def categorize(expense: ExtractedExpense) -> str:
    categories = await _get_categories()
    establishment = expense.establishment or "Not provided"
    description = expense.description or "Not provided"

    prompt = _PROMPT.format(
        categories=", ".join(categories),
        establishment=establishment,
        description=description,
    )

    try:
        raw = await llm.chat_completion(
            model=settings.model_fast,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=20,
        )
        category = raw.strip().rstrip(".")

        if category in categories:
            logger.info("Category: %r (establishment=%r)", category, expense.establishment)
            return category

        for cat in categories:
            if cat.lower() == category.lower():
                return cat

        logger.warning("Invalid category returned by LLM: %r — using Outros", category)
        return "Outros"

    except Exception:
        logger.exception("Categorization failed — using Outros")
        return "Outros"
