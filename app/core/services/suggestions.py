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

    # Only selected types
    stmt = stmt.join(models.User.selected_title_types).join(
        models.Title, models.Title.type_id == models.TitleType.id
    )

    # At least one of the selected genres.
    stmt = stmt.where(
        models.Title.id.in_(
            sa.select(models.title_genre_table.c.title_id)
            .join(
                models.user_genre_table,
                models.user_genre_table.c.genre_id
                == models.title_genre_table.c.genre_id,
            )
            .where(models.user_genre_table.c.user_id == user.id)
        )
    )

    return await session.scalar(stmt)
