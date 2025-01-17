import dataclasses
from collections.abc import Sequence

import sqlalchemy as sa
import sqlalchemy.ext.asyncio as async_sa

from what2watchnextbot import models


@dataclasses.dataclass
class GenrePreferences:
    session: async_sa.AsyncSession
    user: models.User

    async def is_genre_selected(self, genre_id: int) -> bool:
        genre = await self.get_genre_by_id(genre_id)
        selected_genres = await self.user.awaitable_attrs.selected_genres
        return genre in selected_genres

    async def are_all_genres_selected(self) -> bool:
        selected_genres = await self.user.awaitable_attrs.selected_genres
        all_genres = await self.get_all_genres()
        return selected_genres == set(all_genres)

    async def select_genre(self, genre_id: int) -> None:
        genre = await self.get_genre_by_id(genre_id)
        selected_genres = await self.user.awaitable_attrs.selected_genres
        selected_genres.add(genre)

    async def unselect_genre(self, genre_id: int) -> None:
        genre = await self.get_genre_by_id(genre_id)
        selected_genres = await self.user.awaitable_attrs.selected_genres
        selected_genres.discard(genre)

    async def select_all_genres(self) -> None:
        all_genres = await self.get_all_genres()
        selected_genres = await self.user.awaitable_attrs.selected_genres
        selected_genres.update(all_genres)

    async def unselect_all_genres(self) -> None:
        selected_genres = await self.user.awaitable_attrs.selected_genres
        selected_genres.clear()

    async def list_selected_genres(self) -> Sequence[models.Genre]:
        return list(await self.user.awaitable_attrs.selected_genres)

    async def get_all_genres(self) -> Sequence[models.Genre]:
        stmt = sa.select(models.Genre)
        genres = await self.session.scalars(stmt)
        return genres.all()

    async def get_genre_by_id(self, genre_id: int) -> models.Genre:
        genre = await self.session.get(models.Genre, (genre_id,))

        if genre is None:
            msg = f"Genre {genre_id} not found"
            raise ValueError(msg)

        return genre

    async def require_all_selected_genres(self) -> None:
        self.user.require_all_selected_genres = True

    async def require_one_selected_genre(self) -> None:
        self.user.require_all_selected_genres = False

    async def check_all_selected_genres_are_required(self) -> bool:
        return self.user.require_all_selected_genres

    async def get_minimum_rating(self) -> int:
        return self.user.minimum_rating

    async def set_minimum_rating(self, rating: int) -> None:
        self.user.minimum_rating = rating

    async def select_title_type(self, title_type: models.TitleTypes) -> None:
        await self.user.select_title_type(title_type)

    async def unselect_title_type(self, title_type: models.TitleTypes) -> None:
        await self.user.unselect_title_type(title_type)

    async def list_selected_title_types(self) -> Sequence[models.TitleTypes]:
        return await self.user.list_selected_title_types()
