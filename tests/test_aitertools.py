from types import SimpleNamespace
from typing import AsyncGenerator

import pytest

from app import aitertools


async def _async_generator[T](values: list[T]) -> AsyncGenerator[T]:
    for value in values:
        yield value


@pytest.mark.parametrize(
    "attribute_values_it1, attribute_values_it2, expected_matches",
    [
        ([1, 2], [1, 2], [(1, 1), (2, 2)]),
        (
            [1, 2],
            [2],
            [
                (
                    2,
                    2,
                )
            ],
        ),
        (
            [2],
            [1, 2],
            [
                (
                    2,
                    2,
                )
            ],
        ),
        ([1, 2, 3], [2, 3, 4], [(2, 2), (3, 3)]),
    ],
)
async def test_zip_on_same_ordered_attribute(
    attribute_values_it1: list[int],
    attribute_values_it2: list[int],
    expected_matches: list[tuple[int, int]],
) -> None:
    it1 = [SimpleNamespace(attribute=value) for value in attribute_values_it1]
    it2 = [SimpleNamespace(attribute=value) for value in attribute_values_it2]
    it1 = _async_generator(it1)
    it2 = _async_generator(it2)

    actual_matches = aitertools.zip_on_same_ordered_attribute(it1, it2, "attribute")
    actual_matches = [(v1.attribute, v2.attribute) async for v1, v2 in actual_matches]

    assert actual_matches == expected_matches
