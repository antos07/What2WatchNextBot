import aiogram.filters
import aiogram.fsm.scene as scene
import aiogram.types

from what2watchnextbot import database, models
from what2watchnextbot.scenes.suggestionscene import SuggestionScene
from what2watchnextbot.scenes.titlefiltersscene import TitleFilterScene

dispatcher = aiogram.Dispatcher()
scene_registry = scene.SceneRegistry(dispatcher)
scene_registry.add(
    TitleFilterScene,
    SuggestionScene,
)


@dispatcher.update.outer_middleware()
async def provide_sa_session(handler, update, data):
    data["session"] = database.session_factory()
    async with data["session"]:
        return await handler(update, data)


@dispatcher.update.outer_middleware()
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


@dispatcher.message(aiogram.filters.CommandStart())
async def start(message: aiogram.types.Message, scenes: scene.ScenesManager):
    await scenes.enter(SuggestionScene)


@dispatcher.shutdown()
async def shutdown_db():
    await database.engine.dispose()
