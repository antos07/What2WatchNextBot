import datetime

import freezegun
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import Genre, Title, TitleType, User
from app.testing.constants import RANDOM_DATETIME


class TestUser:
    def test_created_at_defaults_to_current_timestamp(self):
        with freezegun.freeze_time(RANDOM_DATETIME):
            user = User(id=1, first_name="test")

        assert user.created_at == RANDOM_DATETIME

    def test_last_activity_at_defaults_to_current_timestamp(
        self, freezer: freezegun.api.FrozenDateTimeFactory
    ):
        freezer.move_to(RANDOM_DATETIME)

        user = User(id=1, first_name="test")
        assert user.last_activity_at == RANDOM_DATETIME

    def test_update_last_activity(self, freezer: freezegun.api.FrozenDateTimeFactory):
        user = User(id=1, first_name="test", last_activity_at=RANDOM_DATETIME)
        new_activity_at = RANDOM_DATETIME + datetime.timedelta(days=1)
        freezer.move_to(new_activity_at)

        user.update_last_activity()

        assert user.last_activity_at == new_activity_at


@pytest.fixture
async def genre(sa_async_session: AsyncSession) -> Genre:
    genre = Genre(name="test")
    sa_async_session.add(genre)
    await sa_async_session.commit()
    await sa_async_session.refresh(genre)
    return genre


class TestGenre:
    def test_hashable(self, genre: Genre) -> None:
        hash(genre)


@pytest.fixture
async def title_type(sa_async_session: AsyncSession) -> TitleType:
    title_type = TitleType(name="movie")
    sa_async_session.add(title_type)
    await sa_async_session.commit()
    await sa_async_session.refresh(title_type)
    return title_type


class TestTitle:
    @pytest.fixture
    async def title(
        self, sa_async_session: AsyncSession, genre: Genre, title_type: TitleType
    ) -> Title:
        title = Title(
            id=1,
            title="A movie",
            type=title_type,
            start_year=2000,
            end_year=2000,
            votes=10000,
            rating=7,
            genres={genre},
        )
        sa_async_session.add(title)
        await sa_async_session.commit()
        await sa_async_session.refresh(title)
        return title

    async def test_relationships_are_displayed_in_repr(
        self,
        title: Title,
        genre: Genre,
        title_type: TitleType,
        sa_async_session: AsyncSession,
    ) -> None:
        sa_async_session.expire(genre)
        sa_async_session.expire(title_type)
        await sa_async_session.refresh(title)

        representation = repr(title)

        assert repr(genre) in representation
        assert repr(title_type) in representation

    def test_hashable(self, title: Title) -> None:
        hash(title)  # no error should be raised


class TestTitleType:
    def test_hashable(self, title_type: TitleType) -> None:
        hash(title_type)  # no error should be raised
