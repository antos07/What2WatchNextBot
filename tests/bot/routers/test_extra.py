import aiogram
from aiogram.methods import AnswerCallbackQuery
from testfixtures.comparison import compare

from app.bot.routers import extra
from app.testing.constants import TG_USER
from app.testing.mockedbot import MockedBot

CALLBACK_QUERY = aiogram.types.CallbackQuery(
    id="id", from_user=TG_USER, data="some data", chat_instance=str(TG_USER.id)
)


async def test_answer_unhandled_callback_query(mocked_bot: MockedBot) -> None:
    await extra.answer_unhandled_callback_query(CALLBACK_QUERY.as_(mocked_bot))

    compare(
        mocked_bot.calls, [AnswerCallbackQuery(callback_query_id=CALLBACK_QUERY.id)]
    )
