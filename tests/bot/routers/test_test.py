from aiogram.methods import SendMessage
from aiogram.types import Chat, Message, User
from testfixtures import compare

from app.bot.routers import test
from app.testing.constants import RANDOM_DATETIME
from app.testing.mockedbot import MockedBot


async def test_ping(mocked_bot: MockedBot) -> None:
    fake_message = Message(
        message_id=1,
        date=RANDOM_DATETIME,
        chat=Chat(id=1, type="private", title="Test"),
        from_user=User(id=1, first_name="Test", is_bot=False),
        text="/ping",
    )

    await test.ping(fake_message.as_(mocked_bot))

    compare(mocked_bot.calls, [SendMessage(chat_id=1, text="pong")])
