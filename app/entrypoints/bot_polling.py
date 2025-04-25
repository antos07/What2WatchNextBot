import asyncio
from collections.abc import Iterable

import aiogram
import pydantic_settings
import sqlalchemy.ext.asyncio as sa_async
from dotenv import load_dotenv

from app import database, logging
from app.bot.bot import create_bot
from app.bot.dispatcher import create_dispatcher
from app.config import Config
from app.logging import logger
from app.redis import create_client as create_redis_client


class PollingConfig(pydantic_settings.BaseSettings, env_prefix="POLLING_"):
    force: bool = False


async def startup(
    bots: Iterable[aiogram.Bot],
    polling_config: PollingConfig,
) -> None:
    logger.info("Starting up...")

    if polling_config.force:
        logger.debug("Deleting webhooks")
        async with asyncio.TaskGroup() as tg:
            for bot in bots:
                tg.create_task(bot.delete_webhook())
        logger.info("Webhooks deleted")


async def shutdown(engine: sa_async.AsyncEngine) -> None:
    logger.info("Shutting down...")

    logger.debug("Disposing engine")
    await engine.dispose()
    logger.info("Engine disposed")

    await logger.complete()


def main() -> None:
    load_dotenv()

    app_config = Config.from_unprefixed_env()
    polling_config = PollingConfig()

    logging.init(app_config.logging)

    redis = create_redis_client(app_config.redis)
    sa_engine, sa_session_factory = database.init_async(app_config.db)
    dispatcher = create_dispatcher(
        config=app_config.dispatcher,
        redis=redis,
        app_config=app_config,
        polling_config=polling_config,
        engine=sa_engine,
        session_factory=sa_session_factory,
    )

    dispatcher.startup.register(startup)
    dispatcher.shutdown.register(shutdown)

    bot = create_bot(config=app_config.bot)
    dispatcher.run_polling(bot, allowed_updates=dispatcher.resolve_used_update_types())


if __name__ == "__main__":
    main()
