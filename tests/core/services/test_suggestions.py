import pytest
from sqlalchemy.ext.asyncio import AsyncSession

import app.core.services.suggestions as suggestion_service
from app.core import models


@pytest.fixture()
def user_without_filters(user: models.User) -> models.User:
    user.minimum_movie_rating = 0
    user.minimum_movie_votes = 0
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
