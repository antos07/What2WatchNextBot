from collections.abc import Callable
from contextlib import suppress
from unittest import mock

import aiogram.types
import pytest
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from app.bot import middlewares
from app.bot.middlewares import ExtendedMiddlewareData
from app.core import models

EVENT = mock.sentinel.event
HANDLER_RETURN_VALUE = mock.sentinel.handler_return_value


async def empty_handler(event: aiogram.types.TelegramObject, data: dict):
    return HANDLER_RETURN_VALUE


class TestSessionProviderMiddleware:
    @pytest.fixture
    def middleware_data(
        self, initialized_db: tuple[AsyncEngine, Callable[[], AsyncSession]]
    ) -> ExtendedMiddlewareData:
        engine, session_factory = initialized_db
        return {
            # keep it as empty as possible to simplify tests
            "engine": engine,
            "session_factory": session_factory,
        }

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
        result = await middlewares.session_provider_middleware(
            empty_handler, EVENT, middleware_data
        )

        assert result == HANDLER_RETURN_VALUE


class TestUpdatedUserProviderMiddleware:
    @pytest.fixture
    def user(self) -> models.User:
        return models.User(id=1, first_name="John")

    @pytest.fixture(autouse=True)
    def patch_user_service(
        self, user: models.User, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        async def patched_create_or_update_from_data(
            session: AsyncSession, user_data: aiogram.types.User
        ) -> models.User:
            return user

        monkeypatch.setattr(
            "app.core.services.user.create_or_update_from_data",
            patched_create_or_update_from_data,
        )

    @pytest.fixture
    def middleware_data(self, sa_async_session: AsyncSession) -> ExtendedMiddlewareData:
        return {
            "session": sa_async_session,
            "event_from_user": aiogram.types.User(
                id=1, is_bot=False, first_name="John"
            ),
        }

    async def test_user_is_injected(
        self, middleware_data: ExtendedMiddlewareData, user: models.User
    ):
        await middlewares.updated_user_provider_middleware(
            empty_handler, EVENT, middleware_data
        )

        assert middleware_data["user"] == user

    async def test_returns_handler_result(
        self, middleware_data: ExtendedMiddlewareData
    ):
        result = await middlewares.updated_user_provider_middleware(
            empty_handler, EVENT, middleware_data
        )

        assert result == HANDLER_RETURN_VALUE
