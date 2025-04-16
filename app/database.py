"""Database initialization.

This module provides functions for initializing SQLAlchemy for usage in sync and
async contexts. Usually only one version of an init function should be called.
"""

from typing import Callable

import pydantic
import pydantic_settings
import sqlalchemy as sa
import sqlalchemy.ext.asyncio as sa_async
import sqlalchemy.orm as orm


class Config(pydantic_settings.BaseSettings, env_prefix="DB_"):
    """Database configuration.

    :ivar dsn: Database connection string.
    """

    dsn: pydantic.PostgresDsn

    @property
    def sqlalchemy_url(self) -> str:
        return str(self.dsn)


def init_sync(config: Config) -> tuple[sa.Engine, Callable[[], orm.Session]]:
    """Initialize SQLAlchemy for usage in sync code (usual SA).

    :param config: Database configuration.
    :return: SQLAlchemy engine and session factory.
    """

    engine = sa.create_engine(config.sqlalchemy_url)
    session_factory = orm.sessionmaker(bind=engine)
    return engine, session_factory


def init_async(
    config: Config,
) -> tuple[sa_async.AsyncEngine, Callable[[], sa_async.AsyncSession]]:
    """Initialize SQLAlchemy for usage in async code (asyncio extension of SA).

    The ``AsyncSession`` is configured using ``Session.expire_on_commit``
    set to ``False`` as recommended in the documentation.

    :param config: Database configuration.
    :return: SQLAlchemy engine and session factory.
    """
    engine = sa_async.create_async_engine(config.sqlalchemy_url)
    session_factory = sa_async.async_sessionmaker(bind=engine, expire_on_commit=False)
    return engine, session_factory
