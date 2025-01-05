import functools

import pydantic
import pydantic_settings


class Settings(pydantic_settings.BaseSettings):
    POSTGRES_DSN: pydantic.PostgresDsn

    BOT_TOKEN: str


@functools.lru_cache
def get_settings() -> Settings:
    return Settings()
