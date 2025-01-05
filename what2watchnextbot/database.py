from collections.abc import Callable

import sqlalchemy as sa
import sqlalchemy.ext.asyncio as async_sa
import sqlalchemy.orm as orm

from what2watchnextbot.settings import get_settings


def setup_async() -> tuple[async_sa.AsyncEngine, Callable[[], async_sa.AsyncSession]]:
    settings = get_settings()

    engine = async_sa.create_async_engine(str(settings.POSTGRES_DSN))
    session_factory = async_sa.async_sessionmaker(bind=engine, expire_on_commit=False)
    return engine, session_factory


def setup_sync() -> tuple[sa.Engine, Callable[[], orm.Session]]:
    settings = get_settings()

    engine = sa.create_engine(str(settings.POSTGRES_DSN))
    session_factory = orm.sessionmaker(bind=engine)
    return engine, session_factory
