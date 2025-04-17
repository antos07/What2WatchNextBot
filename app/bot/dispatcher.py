import aiogram
import pydantic_settings
from aiogram.fsm.storage.redis import (
    DefaultKeyBuilder,
    RedisEventIsolation,
    RedisStorage,
)
from aiogram.fsm.strategy import FSMStrategy
from redis.asyncio import Redis


class Config(pydantic_settings.BaseSettings, env_prefix="DP_"):
    fsm_strategy: FSMStrategy = FSMStrategy.USER_IN_CHAT


def create_dispatcher(config: Config, redis: Redis) -> aiogram.Dispatcher:
    # Use bot id in key builder to avoid collisions with other bots.
    key_builder = DefaultKeyBuilder(with_bot_id=True)

    storage = RedisStorage(redis=redis, key_builder=key_builder)

    # RedisEventIsolation guarantees that at any given moment only one update
    # from the user is being handled
    event_isolation = RedisEventIsolation(redis=redis, key_builder=key_builder)

    return aiogram.Dispatcher(
        storage=storage,
        fsm_strategy=config.fsm_strategy,
        events_isolation=event_isolation,
    )
