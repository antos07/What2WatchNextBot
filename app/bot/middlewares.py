from __future__ import annotations

from typing import TYPE_CHECKING

from aiogram.dispatcher.middlewares.data import MiddlewareData

from app.core import models
from app.core.services import user as user_service

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    import aiogram
    import sqlalchemy.ext.asyncio as sa_async
    from redis.asyncio import Redis

    from app.config import Config

type Handler[T] = Callable[[aiogram.types.TelegramObject, dict], Awaitable[T]]


# Set total=False to allow keys to be missing from the data dict.
class ExtendedMiddlewareData(MiddlewareData, total=False):
    """Middleware data with additional attributes that are
    normally injected as dependencies."""

    engine: sa_async.AsyncEngine
    session_factory: Callable[[], sa_async.AsyncSession]
    redis: Redis
    config: Config
    session: sa_async.AsyncSession
    user: models.User


async def session_provider_middleware[T](
    handler: Handler[T],
    event: aiogram.types.TelegramObject,
    data: ExtendedMiddlewareData,
) -> T:
    """Provide a database session to the handler.

    :param handler: The handler to wrap.
    :param event: The event object.
    :param data: The middleware data.
    :return: The result of the handler.
    """

    session = data["session"] = data["session_factory"]()
    async with session:
        return await handler(event, data)


async def updated_user_provider_middleware[T](
    handler: Handler[T],
    event: aiogram.types.TelegramObject,
    data: ExtendedMiddlewareData,
) -> T:
    """Provide an updated user object to the handler.

    :param handler: The handler to wrap.
    :param event: The event object.
    :param data: The middleware data.
    :return: The result of the handler.
    """

    session = data["session"]
    event_from_user = data["event_from_user"]

    data["user"] = await user_service.create_or_update_from_data(
        session=session, user_data=event_from_user
    )

    return await handler(event, data)
