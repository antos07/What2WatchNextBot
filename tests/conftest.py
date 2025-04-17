from collections.abc import AsyncGenerator

import pydantic
import pytest
import sqlalchemy.ext.asyncio as sa_async

import app.database
from app.core import models


def pytest_addoption(parser: pytest.Parser):
    parser.addoption("--env-file", help="load dotenv file")


@pytest.fixture(scope="session", autouse=True)
def load_env_file(request: pytest.FixtureRequest):
    env_file = request.config.getoption("--env-file")
    if env_file:
        from dotenv import load_dotenv

        load_dotenv(env_file)


@pytest.fixture(scope="session")
def db_config():
    try:
        return app.database.Config()
    except pydantic.ValidationError as e:
        pytest.skip(f"Invalid database configuration. Error: {e}")


@pytest.fixture()
async def sa_async_session(
    db_config: app.database.Config,
) -> AsyncGenerator[sa_async.AsyncSession]:
    engine, session_factory = app.database.init_async(db_config)

    try:
        async with engine.begin() as conn:
            await conn.run_sync(models.Base.metadata.create_all)

        async with session_factory() as session:
            yield session

    finally:
        try:
            async with engine.begin() as conn:
                await conn.run_sync(models.Base.metadata.drop_all)
        finally:
            await engine.dispose()
