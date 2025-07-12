import aiogram
import pytest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

from app.testing import fakes
from app.testing.constants import STORAGE_KEY
from app.testing.mockedbot import MockedBot


@pytest.fixture
def mocked_bot() -> MockedBot:
    return MockedBot()


@pytest.fixture
def fsm_context() -> FSMContext:
    return FSMContext(storage=MemoryStorage(), key=STORAGE_KEY)


@pytest.fixture()
def fake_tg_user(mocked_bot: MockedBot) -> aiogram.types.User:
    return fakes.create_fake_user().as_(mocked_bot)


@pytest.fixture()
def fake_tg_chat(mocked_bot: MockedBot) -> aiogram.types.Chat:
    return fakes.create_fake_chat().as_(mocked_bot)


@pytest.fixture()
def fake_tg_message(
    fake_tg_chat: aiogram.types.Chat,
    fake_tg_user: aiogram.types.User,
    mocked_bot: MockedBot,
) -> aiogram.types.Message:
    return fakes.create_fake_message(from_user=fake_tg_user, chat=fake_tg_chat).as_(
        mocked_bot
    )


@pytest.fixture()
def fake_tg_callback_query(
    fake_tg_user: aiogram.types.User,
    fake_tg_message: aiogram.types.Message,
    mocked_bot: MockedBot,
) -> aiogram.types.CallbackQuery:
    return fakes.create_fake_callback_query(
        from_user=fake_tg_user, message=fake_tg_message
    ).as_(mocked_bot)
