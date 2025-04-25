from typing import Annotated

import aiogram
import aiogram.webhook.aiohttp_server as webhook
import pydantic
import pydantic_settings
import sqlalchemy.ext.asyncio as sa_async
from aiohttp import web
from dotenv import load_dotenv

from app import database, logging
from app.bot.bot import create_bot
from app.bot.dispatcher import create_dispatcher
from app.config import Config
from app.logging import logger
from app.redis import create_client as create_redis_client

type HttpsUrl = Annotated[
    pydantic.HttpUrl, pydantic.UrlConstraints(allowed_schemes=["https"])
]


class WebhookConfig(pydantic_settings.BaseSettings, env_prefix="WEBHOOK_"):
    """Configuration for a bot running in the webhook mode.

    :var external_url: A URL that Telegram will use to send updates.
    :var host: Optional. The IP address, where the webhook will start.
        Default is ``0.0.0.0``.
    :var port: Optional. The port, where the webhook will be listening to.
        Default is ``8000``.
    :var endpoint: Optional. The endpoint, where the webhook will be listening to.
        Default is ``bot``.
    :var certificate: Optional. Path to a self-signed certificate that will be send
        to Telegram.
    :var max_connections: Optional. Maximum allowed number of concurrent connections
        from Telegram. Default is 40.
    """

    external_url: HttpsUrl
    host: pydantic.IPvAnyAddress = "0.0.0.0"
    port: int = 8000
    endpoint: str = "/bot"
    certificate: pydantic.FilePath | None = None
    max_connections: int = 40


async def startup(
    dispatcher: aiogram.Dispatcher,
    bot: aiogram.Bot,
    webhook_config: WebhookConfig,
) -> None:
    logger.info("Starting up...")

    logger.debug("Registering the webhook")
    try:
        await bot.set_webhook(
            url=str(webhook_config.external_url),
            certificate=aiogram.types.FSInputFile(webhook_config.certificate)
            if webhook_config.certificate
            else None,
            max_connections=webhook_config.max_connections,
            allowed_updates=dispatcher.resolve_used_update_types(),
        )
    except Exception as e:
        logger.opt(exception=e).critical("Failed to set webhook")
    else:
        logger.info("Registered the webhook")

    bot_user = await bot.me()
    logger.info(
        f"Running bot @{bot_user.username} id={bot_user.id} - {bot_user.full_name}"
    )


async def shutdown(bot: aiogram.Bot, engine: sa_async.AsyncEngine) -> None:
    logger.info("Shutting down...")

    # Remove webhook
    logger.debug("Removing webhook")
    try:
        await bot.set_webhook("", drop_pending_updates=False)
    except Exception:
        logger.exception("Failed to remove the webhook")
    else:
        logger.info("Removed webhook")

    logger.debug("Disposing engine")
    try:
        await engine.dispose()
    except Exception:
        logger.exception("Failed to dispose the engine")
    else:
        logger.info("Engine disposed")

    await logger.complete()


def main() -> None:
    load_dotenv()

    app_config = Config.from_unprefixed_env()
    webhook_config = WebhookConfig()

    logging.init(app_config.logging)

    redis = create_redis_client(app_config.redis)
    sa_engine, sa_session_factory = database.init_async(app_config.db)
    dispatcher = create_dispatcher(
        config=app_config.dispatcher,
        redis=redis,
        app_config=app_config,
        webhook_config=webhook_config,
        engine=sa_engine,
        session_factory=sa_session_factory,
    )

    dispatcher.startup.register(startup)
    dispatcher.shutdown.register(shutdown)

    bot = create_bot(config=app_config.bot)

    web_app = web.Application()
    webhook.SimpleRequestHandler(dispatcher=dispatcher, bot=bot).register(
        web_app, path=webhook_config.endpoint
    )
    webhook.setup_application(web_app, dispatcher, bot=bot)

    web.run_app(web_app, host=str(webhook_config.host), port=webhook_config.port)


if __name__ == "__main__":
    main()
