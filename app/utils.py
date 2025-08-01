import datetime


async def awaitable[T](arg: T) -> T:
    """Transform any arg to an awaitable.

    Mainly intended to be used in lambdas:

        assert await (lambda n: awaitable(n))(1) == 1
    """

    return arg


def utcnow() -> datetime.datetime:
    """Return the current UTC time."""
    return datetime.datetime.now(datetime.UTC)
