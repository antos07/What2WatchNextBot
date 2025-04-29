import gzip
from pathlib import Path
from random import randint

import httpx
import pytest
from pytest_httpx import HTTPXMock, IteratorStream

from app.imdb.downloads import (
    Datasets,
    DownloadError,
    download_dataset,
    download_multiple_datasets,
)


def compress_gzip_in_parts(data: bytes, parts: int = 2) -> list[bytes]:
    compressed_data = gzip.compress(data)
    part_size = len(compressed_data) // parts

    results = []
    for i in range(parts - 1):
        results.append(compressed_data[i * part_size : (i + 1) * part_size])
    results.append(compressed_data[(parts - 1) * part_size :])
    return results


def compress_gzip_in_incomplete_parts(data: bytes) -> list[bytes]:
    compressed_data = gzip.compress(data)
    return [compressed_data[:-1], compressed_data[-1:]]


async def test_download_dataset(tmp_file_path: Path, httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url="https://datasets.imdbws.com/title.ratings.tsv.gz",
        stream=IteratorStream(compress_gzip_in_parts(b"part 1part 2")),
        headers={"Content-Type": "application/gzip"},
    )

    await download_dataset(Datasets.TITLE_RATINGS, tmp_file_path)

    assert tmp_file_path.read_bytes() == b"part 1part 2"


@pytest.fixture(scope="session")
def large_bytes() -> bytes:
    data = bytearray()
    for _ in range(100 * 1024):
        data.append(randint(0, 255))
    return data


async def test_download_dataset_large_input(
    tmp_file_path: Path, httpx_mock: HTTPXMock, large_bytes: bytes
) -> None:
    httpx_mock.add_response(
        url="https://datasets.imdbws.com/title.ratings.tsv.gz",
        stream=IteratorStream(compress_gzip_in_parts(large_bytes, parts=10)),
        headers={"Content-Type": "application/gzip"},
    )

    await download_dataset(Datasets.TITLE_RATINGS, tmp_file_path)

    assert tmp_file_path.read_bytes() == large_bytes


async def test_download_dataset_raises_download_error_if_httpx_raises_error(
    tmp_file_path: Path, httpx_mock: HTTPXMock
) -> None:
    httpx_mock.add_exception(
        exception=httpx.HTTPError("test error"),
        url="https://datasets.imdbws.com/title.ratings.tsv.gz",
    )

    with pytest.raises(DownloadError):
        await download_dataset(Datasets.TITLE_RATINGS, tmp_file_path)


async def test_download_multiple_datasets(
    tmp_path: Path, httpx_mock: HTTPXMock
) -> None:
    download_path1 = tmp_path / "file1"
    download_path2 = tmp_path / "file2"

    dataset1 = Datasets.TITLE_RATINGS
    dataset2 = Datasets.TITLE_BASICS

    httpx_mock.add_response(
        url="https://datasets.imdbws.com/title.ratings.tsv.gz",
        stream=IteratorStream(compress_gzip_in_parts(b"titleratings")),
        headers={"Content-Type": "application/gzip"},
    )
    httpx_mock.add_response(
        url="https://datasets.imdbws.com/title.basics.tsv.gz",
        stream=IteratorStream(compress_gzip_in_parts(b"titlebasics")),
        headers={"Content-Type": "application/gzip"},
    )

    await download_multiple_datasets(
        [(dataset1, download_path1), (dataset2, download_path2)]
    )

    assert download_path1.read_bytes() == b"titleratings"
    assert download_path2.read_bytes() == b"titlebasics"


async def test_download_multiple_datasets_raises_exception_group(
    tmp_path: Path, httpx_mock: HTTPXMock
) -> None:
    download_path1 = tmp_path / "file1"
    download_path2 = tmp_path / "file2"

    dataset1 = Datasets.TITLE_RATINGS
    dataset2 = Datasets.TITLE_BASICS

    httpx_mock.add_exception(
        exception=httpx.HTTPError("test error"),
        url="https://datasets.imdbws.com/title.ratings.tsv.gz",
    )
    httpx_mock.add_response(
        url="https://datasets.imdbws.com/title.basics.tsv.gz",
        stream=IteratorStream([b"title", b"basics"]),
        headers={"Content-Type": "application/gzip"},
    )

    with pytest.raises(ExceptionGroup) as exc_info:
        await download_multiple_datasets(
            [(dataset1, download_path1), (dataset2, download_path2)]
        )

        assert exc_info.group_contains(DownloadError)
