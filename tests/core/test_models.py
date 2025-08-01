import datetime

import freezegun
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import SKIPPED_TITLE_TIMEOUT
from app.core.models import Genre, Title, TitleSkip, TitleType, User
from app.testing.constants import RANDOM_DATETIME


@pytest.fixture
async def genre(sa_async_session: AsyncSession) -> Genre:
    genre = Genre(name="test")
    sa_async_session.add(genre)
    await sa_async_session.commit()
    await sa_async_session.refresh(genre)
    return genre


@pytest.fixture
async def title_type(sa_async_session: AsyncSession) -> TitleType:
    title_type = TitleType(name="movie")
    sa_async_session.add(title_type)
    await sa_async_session.commit()
    await sa_async_session.refresh(title_type)
    return title_type


class TestUser:
    def test_created_at_defaults_to_current_timestamp(self) -> None:
        with freezegun.freeze_time(RANDOM_DATETIME):
            user = User(id=1, first_name="test")

        assert user.created_at == RANDOM_DATETIME

    def test_last_activity_at_defaults_to_current_timestamp(
        self, freezer: freezegun.api.FrozenDateTimeFactory
    ) -> None:
        freezer.move_to(RANDOM_DATETIME)

        user = User(id=1, first_name="test")
        assert user.last_activity_at == RANDOM_DATETIME

    def test_update_last_activity(
        self, freezer: freezegun.api.FrozenDateTimeFactory
    ) -> None:
        user = User(id=1, first_name="test", last_activity_at=RANDOM_DATETIME)
        new_activity_at = RANDOM_DATETIME + datetime.timedelta(days=1)
        freezer.move_to(new_activity_at)

        user.update_last_activity()

        assert user.last_activity_at == new_activity_at

    @pytest.fixture()
    async def user(self, sa_async_session: AsyncSession) -> User:
        user = User(id=1, first_name="test")
        sa_async_session.add(user)
        await sa_async_session.flush()
        await sa_async_session.refresh(user)
        return user

    async def test_select_genre(
        self, sa_async_session: AsyncSession, genre: Genre, user: User
    ) -> None:
        await user.select_genre(genre)

        assert user.selected_genres == {genre}

    async def test_deselect_genre_with_selected_genre(
        self, sa_async_session: AsyncSession, genre: Genre, user: User
    ) -> None:
        await user.awaitable_attrs.selected_genres  # load selected_genres
        user.selected_genres = {genre}

        await user.deselect_genre(genre)

        assert user.selected_genres == set()

    async def test_deselect_genre_with_unselected_genre(
        self, sa_async_session: AsyncSession, genre: Genre, user: User
    ) -> None:
        await user.deselect_genre(genre)

        assert user.selected_genres == set()

    async def test_select_title_type(
        self, sa_async_session: AsyncSession, title_type: TitleType, user: User
    ) -> None:
        await user.select_title_type(title_type)

        assert user.selected_title_types == {title_type}

    async def test_deselect_title_type_with_selected_title_type(
        self, sa_async_session: AsyncSession, title_type: TitleType, user: User
    ) -> None:
        await user.awaitable_attrs.selected_title_types  # load selected_title_types
        user.selected_title_types = {title_type}

        await user.deselect_title_type(title_type)

        assert user.selected_title_types == set()

    async def test_deselect_title_type_with_unselected_title_type(
        self, sa_async_session: AsyncSession, title_type: TitleType, user: User
    ) -> None:
        await user.deselect_title_type(title_type)

        assert user.selected_title_types == set()

    @freezegun.freeze_time(RANDOM_DATETIME)
    async def test_skip_title_when_not_skipped_yet(
        self, sa_async_session: AsyncSession, title: Title, user: User
    ) -> None:
        await user.skip_title(title)

        await sa_async_session.refresh(user)

        skip = await sa_async_session.get_one(
            TitleSkip, {"user_id": user.id, "title_id": title.id}
        )
        assert skip.expires_at == RANDOM_DATETIME + SKIPPED_TITLE_TIMEOUT
        assert not skip.is_watched

    @freezegun.freeze_time(RANDOM_DATETIME)
    async def test_skip_title_when_already_skipped(
        self, sa_async_session: AsyncSession, title: Title, user: User
    ) -> None:
        sa_async_session.add(
            TitleSkip(
                title=title,
                user=user,
                expires_at=RANDOM_DATETIME + datetime.timedelta(minutes=2),
            )
        )

        await user.skip_title(title)

        await sa_async_session.refresh(user)

        skip = await sa_async_session.get_one(
            TitleSkip, {"user_id": user.id, "title_id": title.id}
        )
        assert skip.expires_at == RANDOM_DATETIME + SKIPPED_TITLE_TIMEOUT
        assert not skip.is_watched


class TestGenre:
    def test_hashable(self, genre: Genre) -> None:
        hash(genre)


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
