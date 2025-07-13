from os import PathLike
from typing import Iterable

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import Genre, Title, TitleType
from app.core.services import title as title_service
from app.core.services.title import refresh_from_imdb
from app.imdb.downloads import Datasets
from app.testing.constants import (
    TITLE_BASICS_DATASET_HEADER,
    TITLE_RATINGS_DATASET_HEADER,
)


class TestGetByIdOrNone:
    async def test_returns_title_when_present(
        self, sa_async_session: AsyncSession, title: Title
    ) -> None:
        assert (
            await title_service.get_by_id_or_none(sa_async_session, title.id) == title
        )

    async def test_returns_none_when_title_not_found(
        self, sa_async_session: AsyncSession
    ) -> None:
        assert await title_service.get_by_id_or_none(sa_async_session, 123) is None


async def test_get_multiple_by_ids(sa_async_session: AsyncSession) -> None:
    titles = [
        Title(
            id=1,
            title="test1",
            type=TitleType(name="movie"),
            start_year=2000,
            end_year=None,
            rating=7,
            votes=10000,
            genres=set(),
        ),
        Title(
            id=2,
            title="test2",
            type=TitleType(name="tvMiniSeries"),
            start_year=2001,
            end_year=None,
            rating=8,
            votes=10000,
            genres=set(),
        ),
        Title(
            id=3,
            title="test3",
            type=TitleType(name="tvSeries"),
            start_year=2002,
            end_year=None,
            rating=9,
            votes=10000,
            genres=set(),
        ),
    ]
    sa_async_session.add_all(titles)

    actual_titles = await title_service.get_multiple_by_ids(sa_async_session, [1, 2])

    assert set(actual_titles) == set(titles[:2])


class TestRefreshFromIMDB:
    @pytest.fixture()
    def title_basics_dataset(self) -> str:
        return (
            TITLE_BASICS_DATASET_HEADER
            + "tt0000001\tmovie\tMovie 1\tMovie 1\t0\t2000\t\\N\t\\N\t"
            "Documentary,Short\n"
            "tt0000002\tmovie\tMovie 2\tMovie 2\t0\t2001\t\\N\t\\N\tFantasy\n"
            "tt0000003\ttvMovie\tMovie 3\tMovie 3\t0\t2002\t\\N\t\\N\tShort\n"
            "tt9999999\tjunk\tjunk\tjunk\t0\t2002\t\\N\t\\N\tShort\n"
        )

    @pytest.fixture()
    def title_ratings_dataset(self) -> str:
        return (
            TITLE_RATINGS_DATASET_HEADER + "tt0000001\t5.7\t2117\n"
            "tt0000002\t8\t200000\n"
            "tt0000003\t7.2\t12345\n"
            "tt9999999\t1\t1\n"
        )

    @pytest.fixture(autouse=True)
    def patch_dataset_downloading(
        self,
        monkeypatch: pytest.MonkeyPatch,
        title_basics_dataset: str,
        title_ratings_dataset: str,
    ):
        async def patched_download_multiple_datasets(
            downloads: Iterable[tuple[Datasets, str | PathLike[str]]],
        ) -> None:
            datasets = {
                Datasets.TITLE_BASICS: title_basics_dataset,
                Datasets.TITLE_RATINGS: title_ratings_dataset,
            }

            for dataset, path in downloads:
                assert dataset in datasets
                with open(path, "w") as f:
                    f.write(datasets[dataset])

        monkeypatch.setattr(
            "app.imdb.downloads.download_multiple_datasets",
            patched_download_multiple_datasets,
        )

    async def test_missing_title_types_are_created(
        self, sa_async_session: AsyncSession
    ) -> None:
        await refresh_from_imdb(sa_async_session)

        title_types_in_db = await sa_async_session.scalars(sa.select(TitleType))
        title_types_in_db = {tt.name for tt in title_types_in_db}
        assert title_types_in_db == {"Movie", "Series", "Mini Series"}

    async def test_existing_title_types_are_used_when_exist(
        self, sa_async_session: AsyncSession
    ) -> None:
        title_types = [
            TitleType(name="Movie"),
            TitleType(name="Series"),
            TitleType(name="Mini Series"),
        ]
        sa_async_session.add_all(title_types)

        await refresh_from_imdb(sa_async_session)

        title_types_in_db = await sa_async_session.scalars(sa.select(TitleType))
        assert set(title_types_in_db) == set(title_types)

    @pytest.fixture()
    def movie_tt(self, sa_async_session: AsyncSession) -> TitleType:
        tt = TitleType(name="Movie")
        sa_async_session.add(tt)
        return tt

    @pytest.fixture()
    def documentary_genre(self, sa_async_session: AsyncSession) -> Genre:
        genre = Genre(name="Documentary")
        sa_async_session.add(genre)
        return genre

    @pytest.fixture()
    def short_genre(self, sa_async_session: AsyncSession) -> Genre:
        genre = Genre(name="Short")
        sa_async_session.add(genre)
        return genre

    @pytest.fixture()
    def fantasy_genre(self, sa_async_session: AsyncSession) -> Genre:
        genre = Genre(name="Fantasy")
        sa_async_session.add(genre)
        return genre

    async def test_new_titles_are_created(
        self,
        sa_async_session: AsyncSession,
        movie_tt: TitleType,
        documentary_genre: Genre,
        short_genre: Genre,
        fantasy_genre: Genre,
    ) -> None:
        await refresh_from_imdb(sa_async_session)

        titles_in_db = await sa_async_session.scalars(
            sa.select(Title).order_by(Title.id)
        )
        titles_in_db = list(titles_in_db)

        expected_titles = [
            Title(
                id=1,
                title="Movie 1",
                type=movie_tt,
                start_year=2000,
                end_year=None,
                rating=5.7,
                votes=2117,
                genres={documentary_genre, short_genre},
            ),
            Title(
                id=2,
                title="Movie 2",
                type=movie_tt,
                start_year=2001,
                end_year=None,
                rating=8.0,
                votes=200000,
                genres={fantasy_genre},
            ),
            Title(
                id=3,
                title="Movie 3",
                type=movie_tt,
                start_year=2002,
                end_year=None,
                rating=7.2,
                votes=12345,
                genres={short_genre},
            ),
        ]

        attributes_to_compare = [
            "id",
            "title",
            "type",
            "start_year",
            "end_year",
            "rating",
            "votes",
            "genres",
        ]
        for attr in attributes_to_compare:
            for title, expected_title in zip(
                titles_in_db, expected_titles, strict=False
            ):
                assert getattr(title, attr) == getattr(expected_title, attr)

    async def test_existing_titles_are_updated(
        self,
        sa_async_session: AsyncSession,
        documentary_genre: Genre,
        short_genre: Genre,
        movie_tt: TitleType,
    ) -> None:
        title_1 = Title(
            id=1,
            title="Movie 1",
            type=movie_tt,
            start_year=1000,
            end_year=None,
            rating=10,
            votes=0,
            genres=set(),
        )
        sa_async_session.add(title_1)

        await refresh_from_imdb(sa_async_session)

        assert title_1.start_year == 2000
        assert title_1.rating == 5.7
        assert title_1.votes == 2117
        assert title_1.genres == {documentary_genre, short_genre}

    async def test_missing_genres_are_created(
        self,
        sa_async_session: AsyncSession,
    ) -> None:
        await refresh_from_imdb(sa_async_session)

        genres_in_db = await sa_async_session.scalars(sa.select(Genre))
        genres_in_db = [genre.name for genre in genres_in_db]

        assert sorted(genres_in_db) == ["Documentary", "Fantasy", "Short"]
