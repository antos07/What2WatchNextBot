import aiogram
from aiogram.fsm.storage.redis import DefaultKeyBuilder, RedisStorage

from what2watchnextbot import database
from what2watchnextbot.routers import error, main, shutdown, startup
from what2watchnextbot.settings import get_settings


def _setup_database(dispatcher: aiogram.Dispatcher) -> None:
    engine, session_factory = database.setup_async()

    dispatcher["engine"] = engine
    dispatcher["session_factory"] = session_factory


def create_dispatcher() -> aiogram.Dispatcher:
    storage = RedisStorage.from_url(
        url=str(get_settings().REDIS_DSN),
        key_builder=DefaultKeyBuilder(with_bot_id=True, with_destiny=True),
    )
    dispatcher = aiogram.Dispatcher(storage=storage)
    _setup_database(dispatcher)

    dispatcher.include_routers(
        main.router,
        startup.router,
        shutdown.router,
        error.router,
    )

    return dispatcher
