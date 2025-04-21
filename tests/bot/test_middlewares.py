from contextlib import suppress
from unittest import mock

import aiogram.types
import pytest

from app.bot import middlewares
from app.bot.middlewares import ExtendedMiddlewareData
from app.core import models

EVENT = mock.sentinel.event


@pytest.fixture
def middleware_data(initialized_db) -> ExtendedMiddlewareData:
    engine, session_factory = initialized_db
    return {
        # keep it as empty as possible to simplify tests
        "engine": engine,
        "session_factory": session_factory,
    }


async def empty_handler(event: aiogram.types.TelegramObject, data: dict):
    pass


class TestSessionProviderMiddleware:
    async def test_session_is_injected(self, middleware_data: ExtendedMiddlewareData):
        await middlewares.session_provider_middleware(
            empty_handler, EVENT, middleware_data
        )
        assert "session" in middleware_data

    async def test_session_is_closed_after_handler_execution(
        self, middleware_data: ExtendedMiddlewareData
    ):
        async def handler(event: aiogram.types.TelegramObject, data: dict) -> None:
            data["session"].add(models.User(id=1, first_name="John"))

        await middlewares.session_provider_middleware(handler, EVENT, middleware_data)

        assert not middleware_data["session"].in_transaction()

    async def test_session_is_closed_after_handler_exception(
        self, middleware_data: ExtendedMiddlewareData
    ):
        async def handler(event: aiogram.types.TelegramObject, data: dict) -> None:
            data["session"].add(models.User(id=1, first_name="John"))
            raise ValueError("Something went wrong")

        with suppress(ValueError):
            await middlewares.session_provider_middleware(
                handler, EVENT, middleware_data
            )

        assert not middleware_data["session"].in_transaction()

    async def test_returns_handler_result(
        self, middleware_data: ExtendedMiddlewareData
    ):
        async def handler(event: aiogram.types.TelegramObject, data: dict) -> int:
            return 1

        result = await middlewares.session_provider_middleware(
            handler, EVENT, middleware_data
        )

        assert result == 1
