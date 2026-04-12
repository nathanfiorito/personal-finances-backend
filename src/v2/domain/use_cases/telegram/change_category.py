from dataclasses import dataclass

from src.v2.domain.ports.notifier_port import NotificationButton, NotifierPort
from src.v2.domain.ports.pending_state_port import PendingStatePort


@dataclass
class ChangeCategoryCommand:
    chat_id: int
    message_id: int
    new_category: str
    new_category_id: int


class ChangeCategory:
    def __init__(self, pending: PendingStatePort, notifier: NotifierPort) -> None:
        self._pending = pending
        self._notifier = notifier

    async def execute(self, cmd: ChangeCategoryCommand) -> None:
        updated = self._pending.update_category(
            cmd.chat_id, cmd.new_category, cmd.new_category_id
        )
        if not updated:
            await self._notifier.edit_message(
                cmd.chat_id, cmd.message_id,
                "⏱️ Operação expirada. Envie a despesa novamente."
            )
            return

        state = self._pending.get(cmd.chat_id)
        if state is None:
            return

        extracted = state.extracted
        amount_str = (
            f"R$ {extracted.amount:,.2f}"
            .replace(",", "X").replace(".", ",").replace("X", ".")
        )
        date_str = (
            extracted.date.strftime("%d/%m/%Y")
            if extracted.date else "data não encontrada"
        )
        lines = [
            f"*{extracted.establishment or 'Estabelecimento desconhecido'}*",
            f"Valor: {amount_str}",
            f"Data: {date_str}",
            f"Categoria: {cmd.new_category}",
        ]
        if extracted.description:
            lines.append(f"Descrição: {extracted.description}")

        buttons = [
            [
                NotificationButton(text="Confirmar ✅", callback_data="confirm"),
                NotificationButton(text="Cancelar ❌", callback_data="cancel"),
            ],
            [
                NotificationButton(
                    text="Alterar Categoria 🏷️", callback_data="edit_category"
                ),
            ],
        ]
        await self._notifier.edit_message(
            cmd.chat_id,
            cmd.message_id,
            "\n".join(lines),
            parse_mode="Markdown",
            buttons=buttons,
        )
