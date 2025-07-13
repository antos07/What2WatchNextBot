from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any

import aiogram
import sqlalchemy.ext.asyncio as sa_async
from aiogram.dispatcher.middlewares.data import MiddlewareData
from redis.asyncio import Redis

from app.core import models
from app.core.services import user as user_service
from app.logging import logger

if TYPE_CHECKING:
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


async def logging_middleware[T](
    handler: Handler[T],
    event: aiogram.types.TelegramObject,
    data: ExtendedMiddlewareData,
) -> T:
    """Provide loguru context for the handler and log the event.

    :param handler: The handler to wrap.
    :param event: The event object.
    :param data: The middleware data.
    :return: The result of the handler.
    """

    context: dict[str, Any] = {}

    if event_update := data.get("event_update"):
        context["update_id"] = event_update.update_id

    event_context = data["event_context"]
    if event_context.user_id:
        context["user_id"] = event_context.user_id
    if event_context.chat_id:
        context["chat_id"] = event_context.chat_id

    with logger.contextualize(**context):
        if event_update:
            logger.debug("Processing update: {!r}", event_update)
        logger.debug("Event: {!r}", event)
        logger.debug("Event context: {!r}", event_context)

        fsm_state = await data["state"].get_state()
        fsm_data = await data["state"].get_data()
        logger.debug(f"FSM state: {fsm_state!r}")
        logger.debug(f"FSM data: {fsm_data}")

        return await handler(event, data)


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
