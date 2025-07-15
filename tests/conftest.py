import random
from collections.abc import AsyncGenerator, Callable
from pathlib import Path

import pydantic
import pytest
import sqlalchemy.ext.asyncio as sa_async
from loguru import logger

import app.database
from app.core import models


def pytest_addoption(parser: pytest.Parser):
    parser.addoption("--env-file", help="load dotenv file")


@pytest.fixture(scope="session", autouse=True)
def constant_random_seed():
    random.seed(42)


@pytest.fixture(scope="session", autouse=True)
def load_env_file(request: pytest.FixtureRequest):
    env_file = request.config.getoption("--env-file")
    if env_file:
        from dotenv import load_dotenv

        load_dotenv(env_file)


@pytest.fixture(scope="session", autouse=True)
def disable_logs_by_default() -> None:
    logger.remove()


@pytest.fixture(scope="session")
def db_config():
    try:
        return app.database.Config()
    except pydantic.ValidationError as e:
        pytest.skip(f"Invalid database configuration. Error: {e}")


@pytest.fixture()
async def initialized_db(
    db_config: app.database.Config,
) -> AsyncGenerator[
    tuple[sa_async.AsyncEngine, Callable[[], sa_async.AsyncSession]], None
]:
    engine, session_factory = app.database.init_async(db_config)

    try:
        async with engine.begin() as conn:
            await conn.run_sync(models.Base.metadata.create_all)

        yield engine, session_factory

    finally:
        try:
            async with engine.begin() as conn:
                await conn.run_sync(models.Base.metadata.drop_all)
        finally:
            await engine.dispose()


@pytest.fixture()
async def sa_async_session(
    db_config: app.database.Config,
    initialized_db: tuple[sa_async.AsyncEngine, Callable[[], sa_async.AsyncSession]],
) -> AsyncGenerator[sa_async.AsyncSession]:
    _, session_factory = initialized_db

    async with session_factory() as session:
        yield session


@pytest.fixture
def tmp_file_path(tmp_path: Path) -> Path:
    return tmp_path / "file"


@pytest.fixture
async def user(sa_async_session: sa_async.AsyncSession) -> models.User:
    user = models.User(id=1, first_name="John")
    sa_async_session.add(user)
    await sa_async_session.commit()
    await sa_async_session.refresh(user)
    return user


@pytest.fixture()
async def title_type(sa_async_session: sa_async.AsyncSession) -> models.TitleType:
    title_type = models.TitleType(name="Test Title Type")
    sa_async_session.add(title_type)
    await sa_async_session.commit()
    await sa_async_session.refresh(title_type)
    return title_type


@pytest.fixture()
async def genre(sa_async_session: sa_async.AsyncSession) -> models.Genre:
    genre = models.Genre(name="Test Genre")
    sa_async_session.add(genre)
    await sa_async_session.commit()
    await sa_async_session.refresh(genre)
    return genre


@pytest.fixture
async def title(
    sa_async_session: sa_async.AsyncSession,
    title_type: models.TitleType,
    genre: models.Genre,
) -> models.Title:
    title = models.Title(
        id=1,
        title="test",
        type=title_type,
        start_year=2000,
        end_year=None,
        rating=7,
        votes=10000,
        genres={genre},
    )
    sa_async_session.add(title)
    await sa_async_session.commit()
    await sa_async_session.refresh(title)
    return title
