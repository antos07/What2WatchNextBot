import pytest
from sqlalchemy.ext.asyncio import AsyncSession

import app.core.services.suggestions as suggestion_service
from app.core import models


@pytest.fixture()
async def other_title_type(sa_async_session: AsyncSession) -> models.TitleType:
    title_type = models.TitleType(name="Other")
    sa_async_session.add(title_type)
    await sa_async_session.commit()
    await sa_async_session.refresh(title_type)
    return title_type


@pytest.fixture()
async def other_genre(sa_async_session: AsyncSession) -> models.Genre:
    genre = models.Genre(name="Other")
    sa_async_session.add(genre)
    await sa_async_session.commit()
    await sa_async_session.refresh(genre)
    return genre


@pytest.fixture()
async def user_without_filters(
    user: models.User,
    title_type: models.TitleType,
    other_title_type: models.TitleType,
    genre: models.Genre,
    other_genre: models.Genre,
) -> models.User:
    user.minimum_movie_rating = 0
    user.minimum_movie_votes = 0

    # Select all title types
    await user.select_title_type(title_type)
    await user.select_title_type(other_title_type)

    # Select all genres
    await user.select_genre(genre)
    await user.select_genre(other_genre)

    return user


async def test_suggest_title_without_filters_when_title_exists(
    sa_async_session: AsyncSession,
    user_without_filters: models.User,
    title: models.Title,
) -> None:
    suggestion = await suggestion_service.suggest_title(
        sa_async_session, user_without_filters
    )

    assert suggestion == title


async def test_suggest_title_without_filters_when_title_doesnt_exist(
    sa_async_session: AsyncSession,
    user_without_filters: models.User,
) -> None:
    suggestion = await suggestion_service.suggest_title(
        sa_async_session, user_without_filters
    )

    assert suggestion is None


async def test_suggest_title_with_minimum_rating_satisfied(
    sa_async_session: AsyncSession,
    user_without_filters: models.User,
    title: models.Title,
) -> None:
    user = user_without_filters
    user.minimum_movie_rating = 5.5
    title.rating = 5.5

    suggestion = await suggestion_service.suggest_title(sa_async_session, user)

    assert suggestion == title


async def test_suggest_title_with_minimum_rating_not_satisfied(
    sa_async_session: AsyncSession,
    user_without_filters: models.User,
    title: models.Title,
) -> None:
    user = user_without_filters
    user.minimum_movie_rating = 5.5
    title.rating = 5.4

    suggestion = await suggestion_service.suggest_title(sa_async_session, user)

    assert suggestion is None


async def test_suggest_title_with_minimum_votes_satisfied(
    sa_async_session: AsyncSession,
    user_without_filters: models.User,
    title: models.Title,
) -> None:
    user = user_without_filters
    user.minimum_movie_votes = 10_000
    title.votes = 10_000

    suggestion = await suggestion_service.suggest_title(sa_async_session, user)

    assert suggestion == title


async def test_suggest_title_with_minimum_votes_not_satisfied(
    sa_async_session: AsyncSession,
    user_without_filters: models.User,
    title: models.Title,
) -> None:
    user = user_without_filters
    user.minimum_movie_votes = 10_000
    title.votes = 9_999

    suggestion = await suggestion_service.suggest_title(sa_async_session, user)

    assert suggestion is None


async def test_suggest_title_only_selected_title_types(
    sa_async_session: AsyncSession,
    user_without_filters: models.User,
    title: models.Title,
) -> None:
    await user_without_filters.deselect_title_type(title.type)

    suggestion = await suggestion_service.suggest_title(
        sa_async_session, user_without_filters
    )
    assert suggestion is None


async def test_suggest_title_at_leat_one_of_selected_genres(
    sa_async_session: AsyncSession,
    user_without_filters: models.User,
    title: models.Title,
    genre: models.Genre,
) -> None:
    await user_without_filters.deselect_genre(genre)

    suggestion = await suggestion_service.suggest_title(
        sa_async_session, user_without_filters
    )
    assert suggestion is None


async def test_suggest_title_all_selected_genres_satisfied(
    sa_async_session: AsyncSession,
    user_without_filters: models.User,
    title: models.Title,
    genre: models.Genre,
    other_genre: models.Genre,
) -> None:
    user = user_without_filters
    user.requires_all_selected_genres = True
    title.genres = {genre, other_genre}

    suggestion = await suggestion_service.suggest_title(sa_async_session, user)
    assert suggestion == title


async def test_suggest_title_all_selected_genres_satisfied_when_subset(
    sa_async_session: AsyncSession,
    user_without_filters: models.User,
    title: models.Title,
    genre: models.Genre,
    other_genre: models.Genre,
) -> None:
    user = user_without_filters
    user.requires_all_selected_genres = True
    await user.deselect_genre(other_genre)
    title.genres = {genre, other_genre}

    suggestion = await suggestion_service.suggest_title(sa_async_session, user)
    assert suggestion == title


async def test_suggest_title_all_selected_genres_not_satisfied(
    sa_async_session: AsyncSession,
    user_without_filters: models.User,
    title: models.Title,
) -> None:
    user = user_without_filters
    user.requires_all_selected_genres = True

    suggestion = await suggestion_service.suggest_title(sa_async_session, user)
    assert suggestion is None
