import typing

import sqlalchemy as sa
import sqlalchemy.ext.asyncio as sa_async

from app.core import models


async def get_by_id(session: sa_async.AsyncSession, user_id: int) -> models.User:
    """Get a user by its ID.

    :param session: SQLAlchemy async session.
    :param user_id: User ID.
    :return: User object.
    :raise ValueError: If user is not found.
    """

    try:
        return await session.get_one(models.User, (user_id,))
    except sa.exc.NoResultFound:
        msg = f"User with id={user_id} not found"
        raise ValueError(msg) from None


async def get_by_id_or_none(
    session: sa_async.AsyncSession, user_id: int
) -> models.User | None:
    """Get a user by its ID or return ``None`` if not found.

    :param session: SQLAlchemy async session.
    :param user_id: User ID.
    :return: User object or ``None`` if not found..
    """

    return await session.get(models.User, (user_id,))


class UserData(typing.Protocol):
    id: int
    first_name: str
    last_name: str | None
    username: str | None


async def create_or_update_from_data(
    session: sa_async.AsyncSession, user_data: UserData
) -> models.User:
    """Create or update a user from an object of user data.

    :param session: SQLAlchemy async session.
    :param user_data: User data object.
    :return: User object.
    """

    user = await get_by_id_or_none(session, user_data.id)
    if user is None:
        user = models.User(id=user_data.id, first_name=user_data.first_name)
        session.add(user)

    user.first_name = user_data.first_name
    user.last_name = user_data.last_name
    user.username = user_data.username

    return user
