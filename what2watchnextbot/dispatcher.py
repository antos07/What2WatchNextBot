import aiogram

from what2watchnextbot import database
from what2watchnextbot.routers import error, main, shutdown


def _setup_database(dispatcher: aiogram.Dispatcher) -> None:
    engine, session_factory = database.setup_async()

    dispatcher["engine"] = engine
    dispatcher["session_factory"] = session_factory


def create_dispatcher() -> aiogram.Dispatcher:
    dispatcher = aiogram.Dispatcher()
    _setup_database(dispatcher)

    dispatcher.include_routers(
        main.router,
        shutdown.router,
        error.router,
    )

    return dispatcher
