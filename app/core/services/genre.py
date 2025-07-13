from typing import cast

import sqlalchemy as sa
import sqlalchemy.ext.asyncio as sa_async

from app.core import models


async def list_all(session: sa_async.AsyncSession) -> list[models.Genre]:
    """List all genres.

    :param session: An SQLAlchemy async session.
    :return: A list of all genres.
    """

    stmt = sa.select(models.Genre)
    return list(await session.scalars(stmt))


async def get_by_id(
    session: sa_async.AsyncSession,
    genre_id: int,
) -> models.Genre:
    """Get genre by ID.

    :param session: An SQLAlchemy async session.
    :param genre_id: Genre ID.
    :return: A genre.
    """
    return cast(models.Genre, await session.get_one(models.Genre, genre_id))
