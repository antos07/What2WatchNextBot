import aiogram

from what2watchnextbot.routers import main, shutdown


def create_dispatcher() -> aiogram.Dispatcher:
    dispatcher = aiogram.Dispatcher()

    dispatcher.include_routers(
        main.router,
        shutdown.router,
    )

    return dispatcher
