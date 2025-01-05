from venv import logger

import aiogram.filters.callback_data as cd
import aiogram.types
import aiogram.utils.formatting as fmt
import aiogram.utils.keyboard as kb
import sqlalchemy.ext.asyncio as async_sa
from aiogram.fsm.scene import Scene, on

from what2watchnextbot import models
from what2watchnextbot.genrepreferences import GenrePreferences


class SelectGenreCD(cd.CallbackData, prefix="select_genre"):
    genre_id: int
    selected: bool


class SelectAllGenresCD(cd.CallbackData, prefix="select_all_genres"):
    selected: bool


class TitleFilterScene(Scene, state="title_filter"):
    CLOSE_SETTINGS_BTN = "Close Settings"

    @on.message.enter()
    async def on_enter(
        self,
        message: aiogram.types.Message,
        session: async_sa.AsyncSession,
        current_user: models.User,
    ):
        genre_preferences = GenrePreferences(session, current_user)

        await self._answer_with_settings_menu(message, genre_preferences)
        logger.info("Displayed settings")

        current_user.record_settings_update()
        await session.commit()

    @on.callback_query(SelectGenreCD.filter())
    async def on_selected_genre(
        self,
        callback_query: aiogram.types.CallbackQuery,
        callback_data: SelectGenreCD,
        session: async_sa.AsyncSession,
        current_user: models.User,
    ) -> None:
        preferences = GenrePreferences(session, current_user)

        if callback_data.selected:
            await preferences.select_genre(callback_data.genre_id)
            logger.info(f"Selected genre id={callback_data.genre_id}")
        else:
            await preferences.unselect_genre(callback_data.genre_id)
            logger.info(f"Unselected genre id={callback_data.genre_id}")

        await session.commit()

        await self._update_genre_selector(
            message=callback_query.message, genre_preferences=preferences
        )

        current_user.record_settings_update()
        await session.commit()

    @on.callback_query(SelectAllGenresCD.filter())
    async def on_select_all_genres(
        self,
        callback_query: aiogram.types.CallbackQuery,
        callback_data: SelectAllGenresCD,
        session: async_sa.AsyncSession,
        current_user: models.User,
    ):
        preferences = GenrePreferences(session, current_user)

        if callback_data.selected:
            await preferences.select_all_genres()
            logger.info("Selected all genres")
        else:
            await preferences.unselect_all_genres()
            logger.info("Unselected all genres")

        await session.commit()

        await self._update_genre_selector(callback_query.message, preferences)

        current_user.record_settings_update()
        await session.commit()

    @on.message(aiogram.F.text == CLOSE_SETTINGS_BTN)
    async def on_close(self, message: aiogram.types.Message):
        logger.debug("Closing settings")
        await self.wizard.back()

    async def _answer_with_genre_selector(
        self,
        message: aiogram.types.Message,
        genre_preferences: GenrePreferences,
    ) -> None:
        text = fmt.as_section(
            fmt.Italic("Select Genres"),
            "Requires a title to have at least one of the selected genres",
        ).as_kwargs()
        reply_markup = await self._build_genre_selector_reply_markup(genre_preferences)
        await message.answer(**text, reply_markup=reply_markup)

    @staticmethod
    async def _build_genre_selector_reply_markup(
        genre_preferences: GenrePreferences,
    ) -> aiogram.types.InlineKeyboardButton:
        all_genres = await genre_preferences.get_all_genres()

        builder = kb.InlineKeyboardBuilder()
        for genre in all_genres:
            selected = await genre_preferences.is_genre_selected(genre.id)
            emoji = "✅" if selected else "☑"
            builder.button(
                text=f"{emoji} {genre.name}",
                callback_data=SelectGenreCD(genre_id=genre.id, selected=not selected),
            )
        builder.adjust(2, repeat=True)

        if await genre_preferences.are_all_genres_selected():
            button = aiogram.types.InlineKeyboardButton(
                text="Unselect All",
                callback_data=SelectAllGenresCD(selected=False).pack(),
            )
        else:
            button = aiogram.types.InlineKeyboardButton(
                text="Select All",
                callback_data=SelectAllGenresCD(selected=True).pack(),
            )
        builder.row(button)

        return builder.as_markup()

    async def _answer_with_settings_menu(
        self,
        message: aiogram.types.Message,
        genre_preferences: GenrePreferences,
    ):
        await self._answer_with_settings_title(message)
        await self._answer_with_genre_selector(message, genre_preferences)

    async def _answer_with_settings_title(self, message: aiogram.types.Message):
        text = fmt.Bold("Settings").as_kwargs()
        reply_markup = (
            kb.ReplyKeyboardBuilder()
            .button(text=self.CLOSE_SETTINGS_BTN)
            .as_markup(resize_keyboard=True)
        )
        await message.answer(**text, reply_markup=reply_markup)

    async def _update_genre_selector(
        self,
        message: aiogram.types.Message,
        genre_preferences: GenrePreferences,
    ):
        reply_markup = await self._build_genre_selector_reply_markup(genre_preferences)
        await message.edit_reply_markup(reply_markup=reply_markup)
