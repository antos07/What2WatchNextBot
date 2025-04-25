from typing import Self, Type

import pydantic_settings

import app.bot.bot
import app.bot.dispatcher
import app.database
import app.logging
import app.redis


class Config(pydantic_settings.BaseSettings):
    model_config = pydantic_settings.SettingsConfigDict(
        nested_model_default_partial_update=True
    )

    dispatcher: app.bot.dispatcher.Config
    db: app.database.Config
    redis: app.redis.Config
    logging: app.logging.Config
    bot: app.bot.bot.Config

    @classmethod
    def from_unprefixed_env(cls: Type[Self]) -> Self:
        return cls(
            dispatcher=app.bot.dispatcher.Config(),
            db=app.database.Config(),
            redis=app.redis.Config(),
            logging=app.logging.Config(),
            bot=app.bot.bot.Config(),
        )
