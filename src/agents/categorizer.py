import logging

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

_CATEGORIES_STR = ", ".join(CATEGORIES)

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


async def categorize(expense: ExtractedExpense) -> str:
    estabelecimento = expense.estabelecimento or "Não informado"
    descricao = expense.descricao or "Não informada"

    prompt = _PROMPT.format(
        categories=_CATEGORIES_STR,
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

        if categoria in CATEGORIES:
            logger.info("Categoria: %r (estabelecimento=%r)", categoria, expense.estabelecimento)
            return categoria

        # Tentar match case-insensitive
        for cat in CATEGORIES:
            if cat.lower() == categoria.lower():
                return cat

        logger.warning("Categoria inválida retornada pelo LLM: %r — usando Outros", categoria)
        return "Outros"

    except Exception:
        logger.exception("Falha na categorização — usando Outros")
        return "Outros"
