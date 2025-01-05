import sqlalchemy as sa
import sqlalchemy.ext.asyncio as async_sa
import sqlalchemy.orm as orm

from what2watchnextbot import models
from what2watchnextbot.logging import logger_wraps


@logger_wraps()
async def suggest(session: async_sa.AsyncSession, user: models.User) -> models.Title:
    title = orm.aliased(models.Title, name="title_1")

    titles_with_selected_genres_stmt = (
        sa.select(title.id)
        .join(models.User.selected_genres)
        .join(title, models.Genre.titles)
        .where(models.User.id == user.id)
    )

    if user.require_all_selected_genres:
        filtered_title_ids_stmt = titles_with_selected_genres_stmt.where(
            ~sa.select(models.selected_genres_tabel)
            .where(
                models.selected_genres_tabel.c.user_id == user.id,
                ~sa.select("*")
                .select_from(models.genre_title_table)
                .where(
                    models.genre_title_table.c.title_id == sa.text("title_1.id"),
                    models.genre_title_table.c.genre_id
                    == models.selected_genres_tabel.c.genre_id,
                )
                .exists(),
            )
            .exists()
        )
    else:
        filtered_title_ids_stmt = titles_with_selected_genres_stmt

    filtered_title_ids_stmt = filtered_title_ids_stmt.where(
        ~sa.select(models.watched_titles_table)
        .where(
            models.watched_titles_table.c.title_id == title.id,
            models.watched_titles_table.c.user_id == user.id,
        )
        .exists(),
        ~sa.select(models.ignored_titles_table)
        .where(
            models.ignored_titles_table.c.title_id == title.id,
            models.ignored_titles_table.c.user_id == user.id,
        )
        .exists(),
    )

    stmt = (
        sa.select(models.Title)
        .where(
            models.Title.type == models.TitleTypes.MOVIE,
            models.Title.votes > 10000,
            models.Title.rating >= 6,
        )
        .where(models.Title.id.in_(filtered_title_ids_stmt))
        .order_by(sa.func.random())
        .limit(1)
    )

    title = await session.scalar(stmt)
    return title
