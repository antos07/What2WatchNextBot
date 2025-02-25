from collections.abc import Callable

import sqlalchemy as sa
import sqlalchemy.ext.asyncio as async_sa
import sqlalchemy.orm as orm

from what2watchnextbot.settings import get_settings

ENGINE_CONFIG = {
    # this should fix errors when a connection is closed by the database:
    # https://docs.sqlalchemy.org/en/20/core/pooling.html#disconnect-handling-pessimistic
    "pool_pre_ping": True,
}


def setup_async() -> tuple[async_sa.AsyncEngine, Callable[[], async_sa.AsyncSession]]:
    settings = get_settings()

    engine = async_sa.create_async_engine(str(settings.POSTGRES_DSN), **ENGINE_CONFIG)
    session_factory = async_sa.async_sessionmaker(bind=engine, expire_on_commit=False)
    return engine, session_factory


def setup_sync() -> tuple[sa.Engine, Callable[[], orm.Session]]:
    settings = get_settings()

    engine = sa.create_engine(str(settings.POSTGRES_DSN), **ENGINE_CONFIG)
    session_factory = orm.sessionmaker(bind=engine)
    return engine, session_factory
