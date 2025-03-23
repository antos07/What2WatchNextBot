import functools

import pydantic
import pydantic_settings


class Settings(pydantic_settings.BaseSettings):
    POSTGRES_DSN: pydantic.PostgresDsn
    REDIS_DSN: pydantic.RedisDsn

    BOT_TOKEN: str

    LOG_ERRORS_TO_CHAT_ID: int | None = None


@functools.lru_cache
def get_settings() -> Settings:
    return Settings()
