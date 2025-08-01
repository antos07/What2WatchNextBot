import sqlalchemy as sa
import sqlalchemy.ext.asyncio as sa_async

import app.core.models as models
import app.core.services.title as title_service
from app.utils import utcnow


def _build_filtered_movie_ids_stmt(user: models.User) -> sa.Select:
    """
    Build a query that selects a list of title IDs, where all the user filters
    are applied.

    :param user: A user whose filters should be applied.
    :return: A select query.
    """

    stmt = sa.select(models.Title.id)

    # Apply trivial filters
    stmt = stmt.where(
        models.Title.rating >= user.minimum_movie_rating,
        models.Title.votes >= user.minimum_movie_votes,
    )

    # Only selected types
    stmt = stmt.join(models.User.selected_title_types).join(
        models.Title, models.Title.type_id == models.TitleType.id
    )

    # At least one of the selected genres.
    stmt = (
        stmt.join(models.Title.genres)
        .join(
            models.user_genre_table,
            models.user_genre_table.c.genre_id == models.Genre.id,
        )
        .where(models.user_genre_table.c.user_id == user.id)
    )

    # All selected genres, if required
    if user.requires_all_selected_genres:
        # As the user wants titles that have all the selected genres simultaneously,
        # I am excluding all the titles that don't have some selected genres.
        # That means that they occur among the selected titles less times than the
        # number of selected genres.
        total_number_of_selected_genres_subquery = (
            sa.select(sa.func.count())
            .join(models.User.selected_genres)
            .where(models.User.id == user.id)
            .scalar_subquery()
        )
        stmt = stmt.group_by(models.Title.id).having(
            sa.func.count(models.Genre.id) >= total_number_of_selected_genres_subquery
        )

    # Filter skipped titles
    skipped_titles_ids = sa.select(models.TitleSkip.title_id).where(
        models.TitleSkip.user_id == user.id,
        models.TitleSkip.expires_at.is_(None)
        | (models.TitleSkip.expires_at > utcnow()),
    )
    stmt = stmt.where(models.Title.id.not_in(skipped_titles_ids))

    return stmt


async def suggest_title(
    session: sa_async.AsyncSession, user: models.User
) -> models.Title | None:
    """Suggest a title for a user based on the user's settings and previous choices.

    :param session: An SQLAlchemy session to interact with the database.
    :param user: The user that needs a suggestion.
    :return: A suggested title or ``None`` if there is no appropriate title.
    """

    stmt = (
        sa.select(models.Title)
        .where(models.Title.id.in_(_build_filtered_movie_ids_stmt(user)))
        .order_by(sa.func.random())
        .limit(1)
    )

    return await session.scalar(stmt)


async def skip_suggested_title(
    session: sa_async.AsyncSession, user: models.User, title_id: int
) -> None:
    """Skip a suggested title for a user.

    :param session: An SQLAlchemy session to interact with the database.
    :param user: The user that wants to skip a suggested title.
    :param title_id: The ID of the title to skip.
    """

    title = await title_service.get_by_id_or_none(session, title_id)
    if title:
        await user.skip_title(title)
