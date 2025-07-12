import aiogram
from aiogram.methods import AnswerCallbackQuery
from testfixtures.comparison import compare

from app.bot.routers import extra
from app.testing.mockedbot import MockedBot


async def test_answer_unhandled_callback_query(
    mocked_bot: MockedBot, fake_tg_callback_query: aiogram.types.CallbackQuery
) -> None:
    await extra.answer_unhandled_callback_query(fake_tg_callback_query)

    compare(
        mocked_bot.calls,
        [AnswerCallbackQuery(callback_query_id=fake_tg_callback_query.id)],
    )
