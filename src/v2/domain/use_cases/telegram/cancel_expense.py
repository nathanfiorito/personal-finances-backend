from dataclasses import dataclass

from src.v2.domain.ports.notifier_port import NotifierPort
from src.v2.domain.ports.pending_state_port import PendingStatePort


@dataclass
class CancelExpenseCommand:
    chat_id: int
    message_id: int


class CancelExpense:
    def __init__(self, pending: PendingStatePort, notifier: NotifierPort) -> None:
        self._pending = pending
        self._notifier = notifier

    async def execute(self, cmd: CancelExpenseCommand) -> None:
        self._pending.clear(cmd.chat_id)
        await self._notifier.edit_message(
            cmd.chat_id, cmd.message_id, "❌ Despesa cancelada."
        )
