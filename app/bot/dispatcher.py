import aiogram
import pydantic_settings
from aiogram.fsm.storage.redis import (
    DefaultKeyBuilder,
    RedisEventIsolation,
    RedisStorage,
)
from aiogram.fsm.strategy import FSMStrategy
from redis.asyncio import Redis

from app.bot import middlewares
from app.bot.routers import test


class Config(pydantic_settings.BaseSettings, env_prefix="DP_"):
    fsm_strategy: FSMStrategy = FSMStrategy.USER_IN_CHAT


def create_dispatcher(config: Config, redis: Redis, **kwargs) -> aiogram.Dispatcher:
    """Create a new dispatcher instance from the given configuration.

    :param config: Dispatcher configuration.
    :param redis: Redis client used by the FSM.
    :param kwargs: Additional dependencies to inject into the dispatcher.
    :return: A new dispatcher instance.
    """

    # Use bot id in key builder to avoid collisions with other bots.
    key_builder = DefaultKeyBuilder(with_bot_id=True)

    storage = RedisStorage(redis=redis, key_builder=key_builder)

    # RedisEventIsolation guarantees that at any given moment only one update
    # from the user is being handled
    event_isolation = RedisEventIsolation(redis=redis, key_builder=key_builder)

    dispatcher = aiogram.Dispatcher(
        storage=storage,
        fsm_strategy=config.fsm_strategy,
        events_isolation=event_isolation,
    )

    # Setup middlewares
    dispatcher.update.outer_middleware.register(middlewares.session_provider_middleware)
    dispatcher.update.outer_middleware.register(middlewares.updated_user_provider_middleware)

    # Setup routers
    dispatcher.include_routers(
        test.router,
    )

    # Inject dependencies
    dispatcher["redis"] = redis
    for key, value in kwargs.items():
        dispatcher[key] = value

    return dispatcher
