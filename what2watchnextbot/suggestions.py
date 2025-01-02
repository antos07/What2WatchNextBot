import sqlalchemy as sa
import sqlalchemy.ext.asyncio as async_sa

from what2watchnextbot import models


async def suggest(session: async_sa.AsyncSession) -> models.Title:
    stmt = (
        sa.select(models.Title)
        .where(
            models.Title.type == models.TitleTypes.MOVIE,
            models.Title.votes > 10000,
            models.Title.rating >= 6,
        )
        .order_by(sa.func.random())
        .limit(1)
    )
    return await session.scalar(stmt)
