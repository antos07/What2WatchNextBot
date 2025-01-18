import collections.abc as col_abc
import itertools
import os
import pathlib
import urllib.error
import urllib.request

import pandas as pd
import sqlalchemy as sa
from sqlalchemy import orm
from tqdm import tqdm

from what2watchnextbot import models

TITLE_TYPES_MAPPING = {
    "movie": models.TitleTypes.MOVIE,
    "tvMovie": models.TitleTypes.MOVIE,
    "tvSeries": models.TitleTypes.SERIES,
    "tvMiniSeries": models.TitleTypes.MINI_SERIES,
}
NO_VALUE = "\\N"


def read_dataframe(
    title_basics_dataset: str | os.PathLike[str],
    title_ratings_dataset: str | os.PathLike[str],
) -> pd.DataFrame:
    title_basics_df = pd.read_csv(title_basics_dataset, sep="\t", na_values=NO_VALUE)
    title_ratings_df = pd.read_csv(title_ratings_dataset, sep="\t", na_values=NO_VALUE)

    return pd.merge(title_basics_df, title_ratings_df, how="inner", on="tconst")


def preprocess_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    # Dropping unused columns
    df = df.drop(columns=["originalTitle", "runtimeMinutes", "isAdult"])

    # Leaving only supported types of titles, converting them to models.TitleTypes
    df = df[df["titleType"].isin(TITLE_TYPES_MAPPING)]
    df["titleType"] = df["titleType"].map(TITLE_TYPES_MAPPING)

    # Dropping rows with missing essential values
    df = df[df["startYear"].notna() & df["genres"].notna() & df["primaryTitle"].notna()]

    # Extracting actual ids from tconst column that has the format "tt\d{8}"
    df["id"] = df["tconst"].apply(lambda imdb_id: int(imdb_id.lstrip("t")))
    df = df.drop(columns=["tconst"])
    df = df.set_index("id", drop=False)

    # startYear column actually contains numbers, so casting it to int
    df["startYear"] = df["startYear"].astype(int)

    # genres column is a coma-separated list of genres, so splitting converting it
    # to an actual list
    df["genres"] = df["genres"].apply(lambda genres: genres.strip().split(","))

    return df


def extract_genres(df: pd.DataFrame) -> col_abc.Sequence[str]:
    genres = set()
    for genre_list in df["genres"]:
        genres.update(genre_list)
    return sorted(genres)


def map_genres_to_models(
    session: orm.Session, genres: col_abc.Iterable[str]
) -> col_abc.Mapping[str, models.Genre]:
    genres_in_db = session.scalars(sa.select(models.Genre))
    genres_to_models = {genre.name: genre for genre in genres_in_db}

    for genre in genres:
        if genre in genres_to_models:
            continue

        genres_to_models[genre] = models.Genre(name=genre)
        session.add(genres_to_models[genre])

    return genres_to_models


BATCH_SIZE = 1000


def write_dataframe_to_db(
    df: pd.DataFrame, session: orm.Session, batch_size=BATCH_SIZE
) -> None:
    genres = extract_genres(df)
    genres_to_models = map_genres_to_models(session, genres)

    for batch in itertools.batched(df.iterrows(), n=batch_size):
        rows = [row for _, row in batch]
        title_ids = (row["id"] for row in rows)

        titles = session.scalars(
            sa.select(models.Title)
            .where(models.Title.id.in_(title_ids))
            # to optimize the number of queries
            .options(orm.selectinload(models.Title.genres))
        )
        id2title = {title.id: title for title in titles}

        for row in rows:
            title = id2title.get(row["id"])
            if not title:
                title = models.Title(
                    id=row["id"],
                    title=row["primaryTitle"],
                    type=row["titleType"],
                    start_year=row["startYear"],
                    end_year=row["endYear"] if row["endYear"].is_integer() else None,
                    rating=row["averageRating"],
                    votes=row["numVotes"],
                )
                session.add(title)

            for genre in row["genres"]:
                genre = genres_to_models[genre]
                if genre not in title.genres:
                    title.genres.add(genre)

        session.flush()


def import_imdb_datasets(
    session: orm.Session,
    title_basics_dataset: str | os.PathLike[str],
    title_ratings_dataset: str | os.PathLike[str],
) -> None:
    df = read_dataframe(title_basics_dataset, title_ratings_dataset)
    df = preprocess_dataframe(df)
    write_dataframe_to_db(df, session)


IMDB_DATASET_URL_FORMAT = "https://datasets.imdbws.com/{dataset}"


def download_dataset(
    dataset_name: str,
    output_dir: str | os.PathLike[str],
    overwrite: bool = False,
    progress_bar: bool = False,
) -> os.PathLike[str]:
    url = IMDB_DATASET_URL_FORMAT.format(dataset=dataset_name)

    if progress_bar:
        bar = None

        def update_bar(_, size, total):
            nonlocal bar

            if not bar:
                bar = tqdm(total=total, unit="B", unit_scale=True, desc=dataset_name)
            bar.update(size)
    else:
        update_bar = None

    download_path = os.path.join(output_dir, dataset_name)
    if os.path.exists(download_path) and not overwrite:
        raise FileExistsError(f"{download_path} already exists")

    try:
        urllib.request.urlretrieve(
            url, os.path.join(output_dir, dataset_name), reporthook=update_bar
        )
    except urllib.error.HTTPError as e:
        msg = f"Failed to download {dataset_name}: {e}"
        raise RuntimeError(msg) from e

    return pathlib.Path(download_path)
