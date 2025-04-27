import asyncio
import enum
from collections.abc import Iterable
from os import PathLike

import aiofiles
import httpx

DATASET_URL_FORMAT: str = "https://datasets.imdbws.com/{}"
"""The format string for the dataset URLs."""

CHUNK_SIZE: int = 16 * 1024  # 16 KiB
"""The size of the chunks to download."""


class Datasets(enum.StrEnum):
    """The available datasets.

    :cvar NAME_BASICS: https://developer.imdb.com/non-commercial-datasets/#namebasicstsvgz
    :cvar TITLE_AKAS: https://developer.imdb.com/non-commercial-datasets/#titleakastsvgz
    :cvar TITLE_BASICS: https://developer.imdb.com/non-commercial-datasets/#titlebasicstsvgz
    :cvar TITLE_CREW: https://developer.imdb.com/non-commercial-datasets/#titlecrewtsvgz
    :cvar TITLE_EPISODE: https://developer.imdb.com/non-commercial-datasets/#titleepisodetsvgz
    :cvar TITLE_PRINCIPALS: https://developer.imdb.com/non-commercial-datasets/#titleprincipalstsvgz
    :cvar TITLE_RATINGS: https://developer.imdb.com/non-commercial-datasets/#titleratingstsvgz
    """

    NAME_BASICS = "name.basics.tsv.gz"
    TITLE_AKAS = "title.akas.tsv.gz"
    TITLE_BASICS = "title.basics.tsv.gz"
    TITLE_CREW = "title.crew.tsv.gz"
    TITLE_EPISODE = "title.episode.tsv.gz"
    TITLE_PRINCIPALS = "title.principals.tsv.gz"
    TITLE_RATINGS = "title.ratings.tsv.gz"


class DownloadError(Exception):
    """Raised when a download fails."""


async def _download_dataset(
    client: httpx.AsyncClient, dataset: Datasets, save_to: str | PathLike[str]
) -> None:
    """Download a dataset using the given httpx client and save it to the given path.

    :param client: The httpx client to use for the download.
    :param dataset: The dataset to download.
    :param save_to: The path to save the dataset to.
    :raise DownloadError: If the download fails.
    """

    url = DATASET_URL_FORMAT.format(dataset)
    try:
        async with (
            client.stream("get", url) as response,
            aiofiles.open(save_to, "wb") as output_file,
        ):
            async for chunk in response.aiter_raw(CHUNK_SIZE):
                await output_file.write(chunk)
    except httpx.HTTPError as e:
        raise DownloadError(f"Failed to download {url}") from e


async def download_dataset(dataset: Datasets, save_to: str | PathLike[str]) -> None:
    """Download a dataset using and save it to the given path.

    :param dataset: The dataset to download.
    :param save_to: The path to save the dataset to.
    :raise DownloadError: If the download fails.
    """
    async with httpx.AsyncClient() as client:
        await _download_dataset(client, dataset, save_to)


async def download_multiple_datasets(
    downloads: Iterable[tuple[Datasets, str | PathLike[str]]],
) -> None:
    """Download multiple datasets using and save them to the given paths.

    :param downloads: An iterable of tuples containing the dataset and the path to save
        it to.
    :raises ExceptionGroup[DownloadError]: If one or more downloads fail.
    """

    async with httpx.AsyncClient() as client:
        async with asyncio.TaskGroup() as tg:
            for dataset, save_to in downloads:
                tg.create_task(_download_dataset(client, dataset, save_to))
