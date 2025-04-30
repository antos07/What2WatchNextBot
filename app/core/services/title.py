from collections.abc import Iterable
from pathlib import Path

import aiofiles.tempfile
import asyncstdlib.itertools as aitertools
import sqlalchemy as sa
import sqlalchemy.ext.asyncio as sa_async

from app import aitertools as aitertools_ext
from app.core import models
from app.core.services import genre as genre_service
from app.core.services import title_type as title_type_service
from app.imdb import downloads, parsers

BATCH_SIZE_WHEN_REFRESHING: int = 5000
"""How many titles will be imported at once into the database."""


async def get_by_id_or_none(
    session: sa_async.AsyncSession, title_id: int
) -> models.Title | None:
    """Get a title by its ID.

    :param session: SQLAlchemy async session.
    :param title_id: Title ID.
    :return: Title object or ``None`` if not found.
    """

    return await session.get(models.Title, (title_id,))


async def get_multiple_by_ids(
    session: sa_async.AsyncSession, title_ids: Iterable[int]
) -> list[models.Title]:
    """Get multiple titles by their IDs. Missing titles are ignored.

    :param session: SQLAlchemy async session.
    :param title_ids: Title IDs.
    :return: List of found titles.
    """

    stmt = sa.select(models.Title).where(models.Title.id.in_(title_ids))
    return list(await session.scalars(stmt))


async def refresh_from_imdb(session: sa_async.AsyncSession) -> None:
    """Refresh titles from the actual IMDB dataset.

    :param session: SQLAlchemy async session.
    """

    async with aiofiles.tempfile.TemporaryDirectory() as tmpdir:
        # Download and open datasets
        tmpdir = Path(tmpdir)
        paths = {
            downloads.Datasets.TITLE_BASICS: tmpdir / "title.basics.tsv",
            downloads.Datasets.TITLE_RATINGS: tmpdir / "title.ratings.tsv",
        }
        await downloads.download_multiple_datasets(list(paths.items()))

        title_basics_reader = parsers.aiter_title_basics_dataset(
            paths[downloads.Datasets.TITLE_BASICS]
        )
        title_ratings_reader = parsers.aiter_title_ratings_dataset(
            paths[downloads.Datasets.TITLE_RATINGS]
        )
        joined_reader = aitertools_ext.zip_on_same_ordered_attribute(
            title_basics_reader, title_ratings_reader, "id"
        )

        # Ensure the necessary title types exist
        movie_tt = await title_type_service.get_or_create_by_name(
            session=session, name="Movie"
        )
        series_tt = await title_type_service.get_or_create_by_name(
            session=session, name="Series"
        )
        mini_series_tt = await title_type_service.get_or_create_by_name(
            session=session, name="Mini Series"
        )

        # Create mapping of dataset title types to my title types
        title_types = {
            "movie": movie_tt,
            "tvMovie": movie_tt,
            "tvSeries": series_tt,
            "tvMiniSeries": mini_series_tt,
        }

        # Filter out unknown title types
        records = (
            (title_basics_record, title_ratings_record)
            async for title_basics_record, title_ratings_record in joined_reader
            if title_basics_record.type in title_types
        )

        # Import datasets
        known_genres = await genre_service.list_all(session)
        known_genres = {genre.name: genre for genre in known_genres}
        async for batch in aitertools.batched(records, BATCH_SIZE_WHEN_REFRESHING):
            batch = list(batch)
            title_ids_in_batch = [
                title_basics_record.id for title_basics_record, _ in batch
            ]

            titles_in_db = await get_multiple_by_ids(session, title_ids_in_batch)
            titles_in_db = {title.id: title for title in titles_in_db}

            for title_basics_record, title_ratings_record in batch:
                # Convert genre names to actual models, creating new models if needed.
                title_genres: set[models.Genre] = set()
                for genre in title_basics_record.genres:
                    if genre in known_genres:
                        title_genres.add(known_genres[genre])
                    else:
                        genre = models.Genre(name=genre)
                        session.add(genre)
                        title_genres.add(genre)
                        known_genres[genre.name] = genre

                # Update the title record if it was already present in the database
                # or create a new one
                if title := titles_in_db.get(title_basics_record.id):
                    title.title = title_basics_record.primary_title
                    title.type = title_types[title_basics_record.type]
                    title.start_year = title_basics_record.start_year
                    title.end_year = title_basics_record.end_year
                    title.rating = title_ratings_record.rating
                    title.votes = title_ratings_record.votes
                    title.genres = title_genres
                else:
                    title = models.Title(
                        id=title_basics_record.id,
                        title=title_basics_record.primary_title,
                        type=title_types[title_basics_record.type],
                        start_year=title_basics_record.start_year,
                        end_year=title_basics_record.end_year,
                        rating=title_ratings_record.rating,
                        votes=title_ratings_record.votes,
                        genres=title_genres,
                    )
                    session.add(title)
