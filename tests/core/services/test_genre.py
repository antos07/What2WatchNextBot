import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import Genre
from app.core.services import genre as genre_service


@pytest.fixture
async def genre_list(sa_async_session: AsyncSession) -> list[Genre]:
    genres = [
        Genre(name="test1"),
        Genre(name="test2"),
        Genre(name="test3"),
    ]
    sa_async_session.add_all(genres)
    await sa_async_session.commit()
    sa_async_session.expire_all()
    return genres


async def test_list_all(
    sa_async_session: AsyncSession, genre_list: list[Genre]
) -> None:
    assert await genre_service.list_all(sa_async_session) == genre_list
