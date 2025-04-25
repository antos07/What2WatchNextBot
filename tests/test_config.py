import pytest

from app.config import Config
from app.testing.constants import BOT_TOKEN, DB_URL, REDIS_URL


@pytest.fixture
def configured_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DB_DSN", DB_URL)
    monkeypatch.setenv("REDIS_DSN", REDIS_URL)
    monkeypatch.setenv("BOT_TOKEN", BOT_TOKEN)


def test_config_can_be_created_from_unprefixed_env(configured_env: None) -> None:
    config = Config.from_unprefixed_env()
    assert str(config.db.dsn) == DB_URL
    assert str(config.redis.dsn) == REDIS_URL
    assert config.bot.token.get_secret_value() == BOT_TOKEN


def test_config_nested_models_can_be_partially_filled(
    configured_env: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("LOG_DIAGNOSE", "true")

    config = Config.from_unprefixed_env()
    assert config.logging.diagnose
