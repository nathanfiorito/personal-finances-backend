from dataclasses import dataclass
from typing import Literal

from src.v2.domain.ports.category_repository import CategoryRepository
from src.v2.domain.ports.llm_port import LLMPort
from src.v2.domain.ports.notifier_port import NotificationButton, NotifierPort
from src.v2.domain.ports.pending_state_port import PendingExpense, PendingStatePort


@dataclass
class ProcessMessageCommand:
    chat_id: int
    entry_type: Literal["image", "text", "pdf"]
    image_b64: str | None = None
    text: str | None = None
    message_id: int | None = None


class ProcessMessage:
    def __init__(
        self,
        llm: LLMPort,
        category_repo: CategoryRepository,
        pending: PendingStatePort,
        notifier: NotifierPort,
    ) -> None:
        self._llm = llm
        self._category_repo = category_repo
        self._pending = pending
        self._notifier = notifier

    async def execute(self, cmd: ProcessMessageCommand) -> None:
        # 1. Extract
        if cmd.entry_type == "image" and cmd.image_b64:
            extracted = await self._llm.extract_from_image(cmd.image_b64)
        elif cmd.text:
            extracted = await self._llm.extract_from_text(cmd.text)
        else:
            await self._notifier.send_message(
                cmd.chat_id, "Não consegui processar a mensagem. Tente novamente."
            )
            return

        # 2. Fetch categories + categorize
        categories = await self._category_repo.list_all()
        category_names = [c.name for c in categories]
        category_name = await self._llm.categorize(extracted, category_names)
        category_id = next(
            (c.id for c in categories if c.name == category_name),
            categories[0].id if categories else 1,
        )

        # 3. Store pending state
        state = PendingExpense(
            extracted=extracted,
            category=category_name,
            category_id=category_id,
            chat_id=cmd.chat_id,
            message_id=cmd.message_id,
        )
        self._pending.set(cmd.chat_id, state)

        # 4. Build and send confirmation message
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
            f"Categoria: {category_name}",
        ]
        if extracted.description:
            lines.append(f"Descrição: {extracted.description}")

        buttons = [
            [
                NotificationButton(text="Confirmar ✅", callback_data="confirm"),
                NotificationButton(text="Cancelar ❌", callback_data="cancel"),
            ],
            [
                NotificationButton(text="Alterar Categoria 🏷️", callback_data="edit_category"),
            ],
        ]
        await self._notifier.send_message(
            cmd.chat_id,
            "\n".join(lines),
            parse_mode="Markdown",
            buttons=buttons,
        )
