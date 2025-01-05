import sqlalchemy as sa
import sqlalchemy.ext.asyncio as async_sa

from what2watchnextbot import models
from what2watchnextbot.logging import logger_wraps


@logger_wraps()
async def suggest(session: async_sa.AsyncSession, user: models.User) -> models.Title:
    titles_with_selected_genres_stmt = (
        sa.select(models.Title.id)
        .join(models.User.selected_genres)
        .join(models.Genre.titles)
        .where(models.User.id == user.id)
    )
    stmt = (
        sa.select(models.Title)
        .where(
            models.Title.type == models.TitleTypes.MOVIE,
            models.Title.votes > 10000,
            models.Title.rating >= 6,
        )
        .where(models.Title.id.in_(titles_with_selected_genres_stmt))
        .order_by(sa.func.random())
        .limit(1)
    )
    title = await session.scalar(stmt)
    return title
