import typing
from collections.abc import Awaitable, Callable

import aiogram.types
from loguru import logger

from what2watchnextbot import models
from what2watchnextbot.routers._utils import outer_middleware_for_all_updates


def _create_router() -> aiogram.Router:
    router = aiogram.Router()

    from . import global_commands, scenes

    router.include_routers(
        global_commands.router,
    )

    scenes.register_in_router(router)

    return router


router = _create_router()

type _MiddlewareData = dict[str, typing.Any]
type _MiddlewareEvent = aiogram.types.TelegramObject
type _MiddlewareNextHandler = Callable[
    [aiogram.types.TelegramObject, _MiddlewareData], Awaitable[typing.Any]
]


@outer_middleware_for_all_updates(router)
async def logging(
    handler: _MiddlewareNextHandler, event: _MiddlewareEvent, data: _MiddlewareData
) -> None:
    logger.debug("event={event!r}", event=event)
    logger.debug("data={data!r}", data=data)

    event_update: aiogram.types.Update = data["event_update"]

    update_id = event_update.update_id
    user_id = data["event_from_user"].id
    chat_id = data["event_chat"].id
    context = {
        "update_id": update_id,
        "user_id": user_id,
        "chat_id": chat_id,
    }
    if cq := event_update.callback_query:
        context["callback_query_id"] = cq.id

    with logger.contextualize(**context):
        logger.opt(lazy=True).debug(
            "Update: \n{}", lambda: event_update.model_dump_json(indent=2)
        )

        return await handler(event, data)


@outer_middleware_for_all_updates(router)
async def provide_sa_session(handler, update, data):
    data["session"] = data["session_factory"]()
    async with data["session"]:
        return await handler(update, data)


@outer_middleware_for_all_updates(router)
async def save_current_user(handler, update, data):
    session = data["session"]

    current_user_id = data["event_from_user"].id
    current_user = await session.get(models.User, {"id": current_user_id})
    if not current_user:
        current_user = models.User(id=current_user_id)
        session.add(current_user)
        await session.commit()

    data["current_user"] = current_user
    await handler(update, data)
