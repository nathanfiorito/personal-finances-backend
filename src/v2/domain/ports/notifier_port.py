from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class NotificationButton:
    """A single inline button, adapter-agnostic."""

    text: str
    callback_data: str


class NotifierPort(ABC):
    @abstractmethod
    async def send_message(
        self,
        chat_id: int,
        text: str,
        parse_mode: str | None = None,
        buttons: list[list[NotificationButton]] | None = None,
    ) -> None: ...

    @abstractmethod
    async def send_file(
        self,
        chat_id: int,
        content: bytes,
        filename: str,
        caption: str,
    ) -> None: ...

    @abstractmethod
    async def answer_callback(
        self,
        callback_id: str,
        text: str | None = None,
    ) -> None: ...

    @abstractmethod
    async def edit_message(
        self,
        chat_id: int,
        message_id: int,
        text: str,
        parse_mode: str | None = None,
        buttons: list[list[NotificationButton]] | None = None,
    ) -> None: ...
