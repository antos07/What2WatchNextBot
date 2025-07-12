import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import TitleType
from app.core.services import title_type as title_type_service


@pytest.fixture
async def title_type_list(sa_async_session: AsyncSession) -> list[TitleType]:
    title_types = [
        TitleType(name="test1"),
        TitleType(name="test2"),
        TitleType(name="test3"),
    ]
    sa_async_session.add_all(title_types)
    await sa_async_session.commit()
    sa_async_session.expire_all()
    return title_types


async def test_list_all(
    sa_async_session: AsyncSession, title_type_list: list[TitleType]
) -> None:
    assert await title_type_service.list_all(sa_async_session) == title_type_list


async def test_get_by_id(sa_async_session: AsyncSession, title_type: TitleType) -> None:
    assert (
        await title_type_service.get_by_id(sa_async_session, title_type.id)
        == title_type
    )


async def test_get_or_create_by_name_when_exists(
    sa_async_session: AsyncSession, title_type: TitleType
) -> None:
    assert (
        await title_type_service.get_or_create_by_name(
            session=sa_async_session, name=title_type.name
        )
        == title_type
    )


async def test_get_or_create_by_name_when_not_exists(
    sa_async_session: AsyncSession,
) -> None:
    title_type = await title_type_service.get_or_create_by_name(
        session=sa_async_session, name="test"
    )

    assert title_type.name == "test"
    assert await title_type_service.list_all(sa_async_session) == [title_type]
