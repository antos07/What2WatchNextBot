from pathlib import Path

import aiofiles.tempfile
import sqlalchemy.ext.asyncio as sa_async

from app import aitertools
from app.core import models
from app.core.services import genre as genre_service
from app.core.services import title_type as title_type_service
from app.imdb import downloads, parsers


async def get_by_id_or_none(
    session: sa_async.AsyncSession, title_id: int
) -> models.Title | None:
    """Get a title by its ID.

    :param session: SQLAlchemy async session.
    :param title_id: Title ID.
    :return: Title object or ``None`` if not found.
    """

    return await session.get(models.Title, (title_id,))


async def refresh_from_imdb(session: sa_async.AsyncSession) -> None:
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
        joined_reader = aitertools.zip_on_same_ordered_attribute(
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

        # Import datasets
        known_genres = await genre_service.list_all(session)
        known_genres = {genre.name: genre for genre in known_genres}
        async for title_basics_record, title_ratings_record in joined_reader:
            # Ignore unsupported title types
            if title_basics_record.type not in title_types:
                continue

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
            if title := await get_by_id_or_none(session, title_basics_record.id):
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
