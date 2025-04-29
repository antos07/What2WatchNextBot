import sqlalchemy as sa
import sqlalchemy.ext.asyncio as sa_async

from app.core import models


async def list_all(session: sa_async.AsyncSession) -> list[models.TitleType]:
    """List all title types.

    :param session: An SQLAlchemy async session.
    :return: A list of all title types.
    """

    stmt = sa.select(models.TitleType)
    return list(await session.scalars(stmt))


async def get_or_create_by_name(
    session: sa_async.AsyncSession, name: str
) -> models.TitleType:
    """Get or create a title type by its name.

    :param session: An SQLAlchemy async session.
    :return: A title type object.
    """

    title_type = await session.scalar(
        sa.select(models.TitleType).where(models.TitleType.name == name)
    )
    if not title_type:
        title_type = models.TitleType(name=name)
        session.add(title_type)

    return title_type
