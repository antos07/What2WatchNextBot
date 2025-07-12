import aiogram
import pytest
import sqlalchemy.ext.asyncio as sa_async

from app.core import models
from app.core.services import user as user_service


class TestGetById:
    async def test_returns_existing_user(
        self, sa_async_session: sa_async.AsyncSession, user: models.User
    ) -> None:
        assert await user_service.get_by_id(sa_async_session, user.id) == user

    async def test_raises_value_error_if_user_not_found(
        self, sa_async_session: sa_async.AsyncSession
    ) -> None:
        with pytest.raises(ValueError):
            await user_service.get_by_id(sa_async_session, 123)


class TestGetByIdOrNone:
    async def test_returns_existing_user(
        self, sa_async_session: sa_async.AsyncSession, user: models.User
    ) -> None:
        assert await user_service.get_by_id_or_none(sa_async_session, user.id) == user

    async def test_returns_none_if_user_not_found(
        self, sa_async_session: sa_async.AsyncSession
    ) -> None:
        assert await user_service.get_by_id_or_none(sa_async_session, 123) is None


class TestCreateOrUpdateFromData:
    @pytest.fixture
    def user_data(self) -> aiogram.types.User:
        return aiogram.types.User(
            id=1, is_bot=False, first_name="John", last_name="Doe", username="johndoe"
        )

    async def test_creates_user_if_not_found(
        self, sa_async_session: sa_async.AsyncSession, user_data: aiogram.types.User
    ) -> None:
        user = await user_service.create_or_update_from_data(
            sa_async_session, user_data
        )

        assert user.id == user_data.id
        assert user.first_name == user_data.first_name
        assert user.last_name == user_data.last_name
        assert user.username == user_data.username

    async def test_updates_user_if_found(
        self,
        sa_async_session: sa_async.AsyncSession,
        user_data: aiogram.types.User,
        user: models.User,
    ) -> None:
        updated_user = await user_service.create_or_update_from_data(
            sa_async_session, user_data
        )

        assert updated_user is user
        assert user.first_name == user_data.first_name
        assert user.last_name == user_data.last_name
        assert user.username == user_data.username
