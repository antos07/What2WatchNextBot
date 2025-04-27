from pathlib import Path

import pytest

from app.imdb import parsers

TITLE_BASICS_HEADER = (
    "tconst\ttitleType\tprimaryTitle\toriginalTitle\tisAdult\tstartYear\t"
    "endYear\truntimeMinutes\tgenres\n"
)
TITLE_RATINGS_HEADER = "tconst\taverageRating\tnumVotes\n"


@pytest.mark.parametrize(
    "dataset, expected_records",
    [
        pytest.param(
            TITLE_BASICS_HEADER
            + "tt0000001\tshort\tCarmencita\tCarmencita\t0\t1894\t\\N\t"
            "1\tDocumentary,Short",
            [
                parsers.TitleBasicsRecord(
                    id=1,
                    type="short",
                    primary_title="Carmencita",
                    start_year=1894,
                    end_year=None,
                    genres=["Documentary", "Short"],
                )
            ],
            id='single record with "endYear" set to null',
        ),
        pytest.param(
            TITLE_BASICS_HEADER + "tt4780148\ttvMiniSeries\tTwo Refugees and a Blonde\t"
            "Two Refugees and a Blonde\t0\t2015\t2015\t65\tComedy",
            [
                parsers.TitleBasicsRecord(
                    id=4780148,
                    type="tvMiniSeries",
                    primary_title="Two Refugees and a Blonde",
                    start_year=2015,
                    end_year=2015,
                    genres=["Comedy"],
                )
            ],
            id="single record no nulls",
        ),
        pytest.param(
            TITLE_BASICS_HEADER
            + "tt4779272\tmovie\tB.E.K.\tB.E.K.\t0\t\\N\t\\N\t\\N\tHorror",
            [],
            id='missing "startYear"',
        ),
        pytest.param(
            TITLE_BASICS_HEADER
            + "\\N\tmovie\tB.E.K.\tB.E.K.\t0\t2000\t\\N\t\\N\tHorror",
            [],
            id='missing "ttconst"',
        ),
        pytest.param(
            TITLE_BASICS_HEADER
            + "tt4779272\t\\N\tB.E.K.\tB.E.K.\t0\t2000\t\\N\t\\N\tHorror",
            [],
            id='missing "titleType"',
        ),
        pytest.param(
            TITLE_BASICS_HEADER
            + "tt4779272\tmovie\t\\N\tB.E.K.\t0\t2000\t\\N\t\\N\tHorror",
            [],
            id='missing "primaryTitle"',
        ),
        pytest.param(
            TITLE_BASICS_HEADER
            + "tt4779272\tmovie\tB.E.K.\tB.E.K.\t0\t2000\t\\N\t\\N\t\\N",
            [],
            id='missing "genres"',
        ),
        pytest.param(
            TITLE_BASICS_HEADER
            + "tt0000001\tshort\tCarmencita\tCarmencita\t0\t1894\t\\N\t"
            "1\tDocumentary,Short\n"
            + "tt4780148\ttvMiniSeries\tTwo Refugees and a Blonde\t"
            "Two Refugees and a Blonde\t0\t2015\t2015\t65\tComedy",
            [
                parsers.TitleBasicsRecord(
                    id=1,
                    type="short",
                    primary_title="Carmencita",
                    start_year=1894,
                    end_year=None,
                    genres=["Documentary", "Short"],
                ),
                parsers.TitleBasicsRecord(
                    id=4780148,
                    type="tvMiniSeries",
                    primary_title="Two Refugees and a Blonde",
                    start_year=2015,
                    end_year=2015,
                    genres=["Comedy"],
                ),
            ],
            id="multiple records",
        ),
    ],
)
async def test_aiter_title_basics_dataset(
    dataset: str, expected_records: list[parsers.TitleBasicsRecord], tmp_file_path: Path
) -> None:
    tmp_file_path.write_text(dataset)

    actual_records = [
        record async for record in parsers.aiter_title_basics_dataset(tmp_file_path)
    ]

    assert actual_records == expected_records


@pytest.mark.parametrize(
    "dataset, expected_records",
    [
        pytest.param(
            TITLE_RATINGS_HEADER + "tt0000001\t5.7\t2117\n",
            [parsers.TitleRatingsRecord(id=1, rating=5.7, votes=2117)],
            id="single record",
        ),
        pytest.param(
            TITLE_RATINGS_HEADER + "\\N\t5.7\t2117\n",
            [],
            id="missing ttconst",
        ),
        pytest.param(
            TITLE_RATINGS_HEADER + "tt0000001\t\\N\t2117\n",
            [],
            id="missing averageRating",
        ),
        pytest.param(
            TITLE_RATINGS_HEADER + "tt0000001\t5.7\t\\N\n",
            [],
            id="missing numVotes",
        ),
    ],
)
async def test_aiter_title_ratings_dataset(
    dataset: str,
    expected_records: list[parsers.TitleRatingsRecord],
    tmp_file_path: Path,
) -> None:
    tmp_file_path.write_text(dataset)

    actual_records = [
        record async for record in parsers.aiter_title_ratings_dataset(tmp_file_path)
    ]

    assert actual_records == expected_records
