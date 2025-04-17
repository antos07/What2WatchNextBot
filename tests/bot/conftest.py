import pytest

from app.testing.mockedbot import MockedBot


@pytest.fixture
def mocked_bot() -> MockedBot:
    return MockedBot()
