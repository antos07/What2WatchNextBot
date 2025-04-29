from collections.abc import AsyncIterable
from typing import AsyncGenerator


async def zip_on_same_ordered_attribute[T1, T2](
    iterable1: AsyncIterable[T1], iterable2: AsyncIterable[T2], attribute: str
) -> AsyncGenerator[tuple[T1, T2]]:
    """Zip two async iterables matching values in pairs by the given attribute.
    Both iterables must be ordered by the attribute.

    :param iterable1: The first async iterable.
    :param iterable2: The second async iterable.
    :param attribute: The name of the attribute to compare.
    :return: An async generator yielding pairs of items that have the same value
        of the given attribute.
    """

    it1 = aiter(iterable1)
    it2 = aiter(iterable2)

    # Consume the first items from both iterators
    try:
        item1 = await anext(it1)
        item2 = await anext(it2)
    except StopAsyncIteration:
        return

    # Items are expected to be ordered by the attribute. That's why consume
    # the lower one until they are equal. Then yield the two items and continue.
    while True:
        attr1 = getattr(item1, attribute)
        attr2 = getattr(item2, attribute)
        if attr1 < attr2:
            try:
                item1 = await anext(it1)
            except StopAsyncIteration:
                return
        elif attr1 > attr2:
            try:
                item2 = await anext(it2)
            except StopAsyncIteration:
                return
        else:
            yield item1, item2
            try:
                item1 = await anext(it1)
                item2 = await anext(it2)
            except StopAsyncIteration:
                return
