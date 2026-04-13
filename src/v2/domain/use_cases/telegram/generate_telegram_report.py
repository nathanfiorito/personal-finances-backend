from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from src.v2.domain.ports.expense_repository import ExpenseRepository
from src.v2.domain.ports.llm_port import LLMPort
from src.v2.domain.ports.notifier_port import NotifierPort


@dataclass
class GenerateTelegramReportCommand:
    chat_id: int
    period_label: str
    start: date
    end: date


class GenerateTelegramReport:
    def __init__(
        self,
        repo: ExpenseRepository,
        llm: LLMPort,
        notifier: NotifierPort,
    ) -> None:
        self._repo = repo
        self._llm = llm
        self._notifier = notifier

    async def execute(self, cmd: GenerateTelegramReportCommand) -> None:
        expenses = await self._repo.list_by_period(cmd.start, cmd.end)

        if not expenses:
            await self._notifier.send_message(
                cmd.chat_id,
                f"Nenhuma despesa encontrada para o período: {cmd.period_label}.",
            )
            return

        # Aggregate by category
        totals: dict[str, Decimal] = {}
        grand_total = Decimal("0")
        for expense in expenses:
            totals[expense.category] = (
                totals.get(expense.category, Decimal("0")) + expense.amount
            )
            grand_total += expense.amount

        # Generate LLM insight
        insight = await self._llm.generate_report(expenses, cmd.period_label)

        # Format report
        lines = [f"📊 *Relatório — {cmd.period_label}*", ""]
        for cat, total in sorted(totals.items(), key=lambda x: x[1], reverse=True):
            pct = (total / grand_total * 100) if grand_total else Decimal("0")
            total_str = (
                f"R$ {total:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            )
            lines.append(f"• {cat}: {total_str} ({pct:.0f}%)")

        grand_str = (
            f"R$ {grand_total:,.2f}"
            .replace(",", "X").replace(".", ",").replace("X", ".")
        )
        lines += ["", f"*Total: {grand_str}*", "", f"💡 {insight}"]

        await self._notifier.send_message(
            cmd.chat_id, "\n".join(lines), parse_mode="Markdown"
        )
