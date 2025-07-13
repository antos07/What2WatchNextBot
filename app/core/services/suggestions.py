import sqlalchemy as sa
import sqlalchemy.ext.asyncio as sa_async

import app.core.models as models


async def suggest_title(
    session: sa_async.AsyncSession, user: models.User
) -> models.Title | None:
    """Suggest a title for a user based on the user's settings and previous choices.

    :param session: An SQLAlchemy session to interact with the database.
    :param user: The user that needs a suggestion.
    :return: A suggested title or ``None`` if there is no appropriate title.
    """

    stmt = sa.select(models.Title).order_by(sa.func.random()).limit(1)

    # Apply trivial filters
    stmt = stmt.where(
        models.Title.rating >= user.minimum_movie_rating,
        models.Title.votes >= user.minimum_movie_votes,
    )

    # TODO: selected genres, selected types

    return await session.scalar(stmt)
