from dataclasses import dataclass

from src.v2.domain.ports.expense_repository import ExpenseRepository
from src.v2.domain.ports.llm_port import LLMPort
from src.v2.domain.ports.notifier_port import NotificationButton, NotifierPort
from src.v2.domain.ports.pending_state_port import PendingStatePort


@dataclass
class ConfirmExpenseCommand:
    chat_id: int
    message_id: int
    skip_duplicate_check: bool = False


class ConfirmExpense:
    def __init__(
        self,
        repo: ExpenseRepository,
        llm: LLMPort,
        pending: PendingStatePort,
        notifier: NotifierPort,
    ) -> None:
        self._repo = repo
        self._llm = llm
        self._pending = pending
        self._notifier = notifier

    async def execute(self, cmd: ConfirmExpenseCommand) -> None:
        state = self._pending.get(cmd.chat_id)
        if state is None:
            await self._notifier.edit_message(
                cmd.chat_id, cmd.message_id,
                "⏱️ Operação expirada. Envie novamente."
            )
            return

        if not cmd.skip_duplicate_check:
            await self._notifier.edit_message(
                cmd.chat_id, cmd.message_id, "⏳ Verificando duplicidades..."
            )
            recent = await self._repo.get_recent(3)
            duplicate_reason = await self._llm.check_duplicate(state.extracted, recent)
            if duplicate_reason:
                buttons = [[
                    NotificationButton(
                        text="Salvar mesmo assim", callback_data="force_confirm"
                    ),
                    NotificationButton(text="Cancelar ❌", callback_data="cancel"),
                ]]
                await self._notifier.edit_message(
                    cmd.chat_id,
                    cmd.message_id,
                    f"⚠️ *Possível duplicidade detectada*\n\n{duplicate_reason}\n\nDeseja salvar mesmo assim?",
                    parse_mode="Markdown",
                    buttons=buttons,
                )
                return

        # Save
        await self._notifier.edit_message(
            cmd.chat_id, cmd.message_id, "⏳ Gravando no banco de dados..."
        )
        try:
            expense = await self._repo.save(state.extracted, state.category_id)
            self._pending.clear(cmd.chat_id)
            amount_str = (
                f"R$ {expense.amount:,.2f}"
                .replace(",", "X").replace(".", ",").replace("X", ".")
            )
            await self._notifier.send_message(
                cmd.chat_id,
                f"✅ Despesa de *{amount_str}* em *{expense.category}* registrada com sucesso!",
                parse_mode="Markdown",
            )
        except Exception:
            await self._notifier.send_message(
                cmd.chat_id, "❌ Erro ao salvar a despesa. Tente novamente."
            )
