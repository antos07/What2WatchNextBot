from pathlib import Path

import httpx
import pytest
from pytest_httpx import HTTPXMock, IteratorStream

from app.imdb.downloads import (
    Datasets,
    DownloadError,
    download_dataset,
    download_multiple_datasets,
)


async def test_download_dataset(tmp_file_path: Path, httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url="https://datasets.imdbws.com/title.ratings.tsv.gz",
        stream=IteratorStream([b"part 1", b"part 2"]),
        headers={"Content-Type": "application/gzip"},
    )

    await download_dataset(Datasets.TITLE_RATINGS, tmp_file_path)

    assert tmp_file_path.read_bytes() == b"part 1part 2"


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
        stream=IteratorStream([b"title", b"ratings"]),
        headers={"Content-Type": "application/gzip"},
    )
    httpx_mock.add_response(
        url="https://datasets.imdbws.com/title.basics.tsv.gz",
        stream=IteratorStream([b"title", b"basics"]),
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
