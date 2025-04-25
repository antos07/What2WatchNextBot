import pydantic
import pydantic_settings
from redis.asyncio import Redis


class Config(pydantic_settings.BaseSettings, env_prefix="REDIS_"):
    dsn: pydantic.RedisDsn


def create_client(config: Config) -> Redis:
    """Create a new Redis client from the given configuration."""

    return Redis.from_url(str(config.dsn))
