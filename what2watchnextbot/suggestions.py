import sqlalchemy as sa
import sqlalchemy.ext.asyncio as async_sa
from loguru import logger

from what2watchnextbot import models
from what2watchnextbot.logging import logger_wraps


def _build_filtered_movie_ids_stmt(user: models.User) -> sa.Select:
    """
    Build a query that selects a list of title IDs, where all the user filters
    are applied.

    :param user: A user whose filters should be applied.
    :return: A select query.
    """

    stmt = sa.select(models.Title.id)

    # Filtering titles that have at least one of user selected genres
    stmt = (
        stmt.join(models.User.selected_genres)
        .join(models.Genre.titles)
        .where(models.User.id == user.id)
    )

    if user.require_all_selected_genres:
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
            sa.func.count(models.Genre.id) == total_number_of_selected_genres_subquery
        )

    # Filtering out watched titles
    stmt = stmt.where(
        ~sa.select("*")
        .select_from(models.watched_titles_table)
        .where(
            models.watched_titles_table.c.title_id == models.Title.id,
            models.watched_titles_table.c.user_id == user.id,
        )
        .exists(),
    )

    # Filtering out ignored titles
    stmt = stmt.where(
        ~sa.select("*")
        .select_from(models.ignored_titles_table)
        .where(
            models.ignored_titles_table.c.title_id == models.Title.id,
            models.ignored_titles_table.c.user_id == user.id,
        )
        .exists(),
    )

    # Leaving only selected title types
    stmt = stmt.where(
        sa.select("*")
        .where(
            models.selected_title_types_table.c.type == models.Title.type,
            models.selected_title_types_table.c.user_id == user.id,
        )
        .exists(),
    )

    # Leaving title with selected minimum rating and minimum number of votes
    stmt = stmt.where(
        models.Title.votes >= user.minimum_votes,
        models.Title.rating >= user.minimum_rating,
    )

    logger.debug("stmt=\n{}", stmt)

    return stmt


@logger_wraps()
async def suggest(session: async_sa.AsyncSession, user: models.User) -> models.Title:
    stmt = (
        sa.select(models.Title)
        .where(models.Title.id.in_(_build_filtered_movie_ids_stmt(user)))
        .order_by(sa.func.random())
        .limit(1)
    )

    title = await session.scalar(stmt)
    return title
