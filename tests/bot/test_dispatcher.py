from unittest import mock

import pytest
from aiogram.fsm.storage.redis import RedisEventIsolation, RedisStorage
from redis.asyncio import Redis

from app.bot import dispatcher


class TestCreateDispatcher:
    @pytest.fixture
    def default_config(self) -> dispatcher.Config:
        return dispatcher.Config()

    @pytest.fixture
    def redis_mock(self) -> mock.MagicMock:
        return mock.MagicMock(spec=Redis)

    def test_fsm_storage_is_redis(
        self, default_config: dispatcher.Config, redis_mock: mock.MagicMock
    ) -> None:
        dp = dispatcher.create_dispatcher(config=default_config, redis=redis_mock)

        assert isinstance(dp.storage, RedisStorage)
        assert dp.storage.redis is redis_mock

    def test_redis_events_isolation_is_enabled(
        self, default_config: dispatcher.Config, redis_mock: mock.MagicMock
    ) -> None:
        dp = dispatcher.create_dispatcher(config=default_config, redis=redis_mock)

        assert isinstance(dp.fsm.events_isolation, RedisEventIsolation)
        assert dp.fsm.events_isolation.redis is redis_mock

    def test_fsm_storage_key_builder_includes_bot_id(
        self, default_config: dispatcher.Config, redis_mock: mock.MagicMock
    ) -> None:
        dp = dispatcher.create_dispatcher(config=default_config, redis=mock.MagicMock())

        assert dp.storage.key_builder.with_bot_id

    def test_redis_events_isolation_key_builder_includes_bot_id(
        self, default_config: dispatcher.Config, redis_mock: mock.MagicMock
    ) -> None:
        dp = dispatcher.create_dispatcher(config=default_config, redis=mock.MagicMock())

        assert dp.fsm.events_isolation.key_builder.with_bot_id
