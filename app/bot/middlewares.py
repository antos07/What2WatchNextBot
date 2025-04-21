from __future__ import annotations

from typing import TYPE_CHECKING

from aiogram.dispatcher.middlewares.data import MiddlewareData

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
