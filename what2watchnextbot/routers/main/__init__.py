import aiogram

from what2watchnextbot import database, models
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


@outer_middleware_for_all_updates(router)
async def provide_sa_session(handler, update, data):
    data["session"] = database.session_factory()
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
