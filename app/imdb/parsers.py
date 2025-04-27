import csv
import io
from collections.abc import AsyncGenerator
from os import PathLike
from typing import NamedTuple, Protocol

import aiofiles


# my guess about the format of IMDB's datasets
class IMDBDialect(csv.Dialect):
    delimiter = "\t"
    doublequote = False
    escapechar = None
    lineterminator = "\n"
    quotechar = None
    quoting = csv.QUOTE_NONE
    skipinitialspace = False
    strict = True


csv.register_dialect("imdb", IMDBDialect)


class _AsyncReadableFile(Protocol):
    async def readline(self) -> str: ...

    async def readlines(self, hint: int | None = -1) -> str: ...


READ_LINES_HINT = 10 * 1024  # 10 KiB
"""How many bytes to read from the file at once."""

MISSING_VALUE = "\\N"
"""The value used to indicate that a value is missing."""


async def _async_reader(afp: _AsyncReadableFile) -> AsyncGenerator[str]:
    """A more performant way to iterate over a file asynchronously.

    Reduces the number of calls into an executor by reading multiple lines at a time.
    The exact number of lines read is determined by the ``READ_LINES_HINT``
    constant - it will read this number of bytes and then until the end of the
    line.

    :param afp: An async file-like object that supports ``readlines()``.
    :return: An async generator that yields lines from the file.
    """

    lines = await afp.readlines(READ_LINES_HINT)
    while lines:
        for line in lines:
            yield line
        lines = await afp.readlines(READ_LINES_HINT)


def _convert_missing_values(row: dict[str, str]) -> dict[str, str | None]:
    return {key: value if value != "\\N" else None for key, value in row.items()}


async def _async_dict_reader(afp: _AsyncReadableFile) -> AsyncGenerator[dict[str, str]]:
    buffer = io.StringIO()
    sync_reader = csv.DictReader(buffer, dialect="imdb")

    header = await afp.readline()
    buffer.write(header)

    async for line in _async_reader(afp):
        buffer.write(line)
        # To make the buffer readable.
        buffer.seek(0)

        # The way it's written should guarantee that StopIteration is never raised.
        # It always has a new line in the buffer before next() is called.
        try:
            yield _convert_missing_values(next(sync_reader))
        except StopIteration:
            raise ValueError("Dataset is broken") from None

        # clear the buffer
        buffer.seek(0)
        buffer.truncate()


def _tconst_to_id(tconst: str) -> int:
    return int(tconst[2:])


class TitleBasicsRecord(NamedTuple):
    """A record of title.basics.tsv.gz dataset.

    :var id: The ID of the title. Inferred from the ``tconst`` column.
    :var type: The type of the title.
    :var primary_title: The title (name) of the title.
    :var start_year: The year the title was released.
    :var end_year: Optional. The year the title was released.
    :var genres: A list of genres associated with the title.
    """

    id: int
    type: str
    primary_title: str
    start_year: int
    end_year: int | None
    genres: list[str]


async def aiter_title_basics_dataset(
    filepath: str | PathLike[str],
) -> AsyncGenerator[TitleBasicsRecord]:
    """An async generator that yields records from the title.basics.tsv.gz dataset.

    :param filepath: The path to the dataset file.
    :return: An async generator that yields records from the dataset.
    """

    async with aiofiles.open(filepath, "r") as dataset_file:
        reader = _async_dict_reader(dataset_file)

        async for row in reader:
            non_none_values = [
                row["tconst"],
                row["titleType"],
                row["primaryTitle"],
                row["startYear"],
                row["genres"],
            ]
            # skip the row if the necessary data is not present
            if all(non_none_values):
                yield TitleBasicsRecord(
                    id=_tconst_to_id(row["tconst"]),
                    type=row["titleType"],
                    primary_title=row["primaryTitle"],
                    start_year=int(row["startYear"]),
                    end_year=int(row["endYear"]) if row["endYear"] else None,
                    genres=row["genres"].split(","),
                )


class TitleRatingsRecord(NamedTuple):
    """A record of title.ratings.tsv.gz dataset.

    :var id: The ID of the title. Inferred from the ``tconst`` column.
    :var rating: The average rating of the title.
    :var votes: The number of votes for the title.
    """

    id: int
    rating: float
    votes: int


async def aiter_title_ratings_dataset(
    filepath: str | PathLike[str],
) -> AsyncGenerator[TitleRatingsRecord]:
    """An async generator that yields records from the title.ratings.tsv.gz dataset.

    :param filepath: The path to the dataset file.
    :return: An async generator that yields records from the dataset.
    """

    async with aiofiles.open(filepath, "r") as dataset_file:
        reader = _async_dict_reader(dataset_file)

        async for row in reader:
            non_none_values = [row["tconst"], row["averageRating"], row["numVotes"]]
            # skip the row if the necessary data is not present
            if all(non_none_values):
                yield TitleRatingsRecord(
                    id=_tconst_to_id(row["tconst"]),
                    rating=float(row["averageRating"]),
                    votes=int(row["numVotes"]),
                )
