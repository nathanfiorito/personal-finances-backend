from dataclasses import dataclass

from fastapi import APIRouter

from src.config.settings import settings as _settings
from src.v2.adapters.primary.bff.routers.categories import router as categories_router
from src.v2.adapters.primary.bff.routers.export import router as export_router
from src.v2.adapters.primary.bff.routers.reports import router as reports_router
from src.v2.adapters.primary.bff.routers.transactions import router as transactions_router
from src.v2.adapters.secondary.memory.pending_state_adapter import (
    InMemoryPendingStateAdapter,
)
from src.v2.adapters.secondary.openrouter.llm_adapter import OpenRouterLLMAdapter
from src.v2.adapters.secondary.supabase.category_repository import (
    SupabaseCategoryRepository,
)
from src.v2.adapters.secondary.supabase.expense_repository import (
    SupabaseExpenseRepository,
)
from src.v2.adapters.secondary.telegram_api.notifier_adapter import (
    TelegramNotifierAdapter,
)
from src.v2.domain.use_cases.categories.create_category import CreateCategory
from src.v2.domain.use_cases.categories.deactivate_category import DeactivateCategory
from src.v2.domain.use_cases.categories.list_categories import ListCategories
from src.v2.domain.use_cases.categories.update_category import UpdateCategory
from src.v2.domain.use_cases.expenses.create_expense import CreateExpense
from src.v2.domain.use_cases.expenses.delete_expense import DeleteExpense
from src.v2.domain.use_cases.expenses.get_expense import GetExpense
from src.v2.domain.use_cases.expenses.list_expenses import ListExpenses
from src.v2.domain.use_cases.expenses.update_expense import UpdateExpense
from src.v2.domain.use_cases.reports.export_csv import ExportCsv
from src.v2.domain.use_cases.reports.get_monthly import GetMonthly
from src.v2.domain.use_cases.reports.get_summary import GetSummary
from src.v2.domain.use_cases.telegram.cancel_expense import CancelExpense
from src.v2.domain.use_cases.telegram.change_category import ChangeCategory
from src.v2.domain.use_cases.telegram.confirm_expense import ConfirmExpense
from src.v2.domain.use_cases.telegram.generate_telegram_report import (
    GenerateTelegramReport,
)
from src.v2.domain.use_cases.telegram.process_message import ProcessMessage


@dataclass
class UseCaseContainer:
    # Expenses
    create_expense: CreateExpense
    list_expenses: ListExpenses
    get_expense: GetExpense
    update_expense: UpdateExpense
    delete_expense: DeleteExpense
    # Categories
    list_categories: ListCategories
    create_category: CreateCategory
    update_category: UpdateCategory
    deactivate_category: DeactivateCategory
    # Reports
    get_summary: GetSummary
    get_monthly: GetMonthly
    export_csv: ExportCsv
    # Telegram flows
    process_message: ProcessMessage
    confirm_expense: ConfirmExpense
    cancel_expense: CancelExpense
    change_category: ChangeCategory
    generate_telegram_report: GenerateTelegramReport


async def build_use_cases() -> UseCaseContainer:
    """Build and wire all adapters and use cases. Called once during lifespan startup."""
    from supabase import acreate_client

    supabase = await acreate_client(
        _settings.supabase_url, _settings.supabase_service_key
    )

    expense_repo = SupabaseExpenseRepository(supabase)
    category_repo = SupabaseCategoryRepository(supabase)
    llm = OpenRouterLLMAdapter(
        model_vision=_settings.model_vision,
        model_fast=_settings.model_fast,
    )
    notifier = TelegramNotifierAdapter(bot_token=_settings.telegram_bot_token)
    pending = InMemoryPendingStateAdapter()

    return UseCaseContainer(
        create_expense=CreateExpense(expense_repo),
        list_expenses=ListExpenses(expense_repo),
        get_expense=GetExpense(expense_repo),
        update_expense=UpdateExpense(expense_repo),
        delete_expense=DeleteExpense(expense_repo),
        list_categories=ListCategories(category_repo),
        create_category=CreateCategory(category_repo),
        update_category=UpdateCategory(category_repo),
        deactivate_category=DeactivateCategory(category_repo),
        get_summary=GetSummary(expense_repo),
        get_monthly=GetMonthly(expense_repo),
        export_csv=ExportCsv(expense_repo),
        process_message=ProcessMessage(llm, category_repo, pending, notifier),
        confirm_expense=ConfirmExpense(expense_repo, llm, pending, notifier),
        cancel_expense=CancelExpense(pending, notifier),
        change_category=ChangeCategory(pending, notifier),
        generate_telegram_report=GenerateTelegramReport(expense_repo, llm, notifier),
    )


def build_v2_router() -> APIRouter:
    """Return an APIRouter with all v2 BFF routes included."""
    router = APIRouter()
    router.include_router(transactions_router)
    router.include_router(categories_router)
    router.include_router(reports_router)
    router.include_router(export_router)
    return router
