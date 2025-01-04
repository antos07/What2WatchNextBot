import aiogram.filters
import aiogram.fsm.scene as scenes
import aiogram.utils.formatting as fmt
import aiogram.utils.keyboard as kb
import sqlalchemy.ext.asyncio as async_sa

from what2watchnextbot import database, models, suggestions
from what2watchnextbot.scenes.titlefiltersscene import TitleFilterScene

dispatcher = aiogram.Dispatcher()
scene_registry = scenes.SceneRegistry(dispatcher)
scene_registry.add(
    TitleFilterScene,
)

dispatcher.message.register(
    TitleFilterScene.as_handler(), aiogram.filters.CommandStart()
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


@dispatcher.message(aiogram.filters.Command("suggest"))
async def cmd_suggest(
    message: aiogram.types.Message,
    session: async_sa.AsyncSession,
    current_user: models.User,
):
    suggested_movie = await suggestions.suggest(session, current_user)

    text = fmt.as_section(
        fmt.Italic(fmt.Bold(suggested_movie.title)),
        fmt.as_key_value(
            "IMDB Rating", f"{suggested_movie.rating} ({suggested_movie.votes} votes)"
        ),
    ).as_kwargs()
    reply_markup = (
        kb.InlineKeyboardBuilder()
        .button(text="IMDB", url=suggested_movie.imdb_url)
        .as_markup()
    )
    await message.answer(**text, reply_markup=reply_markup)


@dispatcher.shutdown()
async def shutdown_db():
    await database.engine.dispose()
