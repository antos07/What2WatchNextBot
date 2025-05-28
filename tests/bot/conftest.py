import pytest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

from app.testing.constants import STORAGE_KEY
from app.testing.mockedbot import MockedBot


@pytest.fixture
def mocked_bot() -> MockedBot:
    return MockedBot()


@pytest.fixture
def fsm_context() -> FSMContext:
    return FSMContext(storage=MemoryStorage(), key=STORAGE_KEY)
