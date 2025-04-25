import pytest

from app import database


@pytest.fixture
def db_config() -> database.Config:
    return database.Config(dsn="postgresql+psycopg://user:password@localhost:5432/db")


class TestInitSync:
    def test_engine_is_configured_with_a_valid_url(self, db_config: database.Config):
        engine, _ = database.init_sync(db_config)
        assert (
            engine.url.render_as_string(hide_password=False) == db_config.sqlalchemy_url
        )


class TestInitAsync:
    def test_engine_is_configured_with_a_valid_url(self, db_config: database.Config):
        engine, _ = database.init_async(db_config)
        assert (
            engine.url.render_as_string(hide_password=False) == db_config.sqlalchemy_url
        )

    def test_session_is_configured_with_expire_on_commit_set_to_false(
        self, db_config: database.Config
    ):
        _, session_factory = database.init_async(db_config)

        session = session_factory()
        assert not session.sync_session.expire_on_commit
