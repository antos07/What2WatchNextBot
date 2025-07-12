from typing import Literal

import aiogram

from app.testing.constants import RANDOM_DATETIME

UNSPECIFIED = object()


def create_fake_user(
    id: int = 1, first_name: str = "John", is_bot: bool = False
) -> aiogram.types.User:
    return aiogram.types.User(id=id, first_name=first_name, is_bot=is_bot)


def create_fake_chat(
    id: int = 2,
    title: str = "John",
    type: aiogram.enums.ChatType = aiogram.enums.ChatType.PRIVATE,
) -> aiogram.types.Chat:
    return aiogram.types.Chat(id=id, title=title, type=type)


def create_fake_message(
    message_id: int = 3,
    text: str = "fake message",
    from_user: aiogram.types.User | None = None,
    chat: aiogram.types.Chat | None = None,
) -> aiogram.types.Message:
    return aiogram.types.Message(
        message_id=message_id,
        text=text,
        from_user=from_user or create_fake_user(),
        chat=chat or create_fake_chat(),
        date=RANDOM_DATETIME,
    )


def create_fake_callback_query(
    id: str = "4",
    data: str = "fake data",
    chat_instance: str = "fake chat",
    from_user: aiogram.types.User | None = None,
    message: aiogram.types.Message | None | Literal[UNSPECIFIED] = UNSPECIFIED,
) -> aiogram.types.CallbackQuery:
    return aiogram.types.CallbackQuery(
        id=id,
        data=data,
        chat_instance=chat_instance,
        from_user=from_user or create_fake_user(),
        message=message if message is not UNSPECIFIED else create_fake_message(),
    )
