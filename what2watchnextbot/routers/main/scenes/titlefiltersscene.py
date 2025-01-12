import aiogram.exceptions
import aiogram.filters.callback_data as cd
import aiogram.types
import aiogram.utils.formatting as fmt
import aiogram.utils.keyboard as kb
import sqlalchemy.ext.asyncio as async_sa
from aiogram.fsm.scene import Scene, on
from loguru import logger

from what2watchnextbot import models
from what2watchnextbot.genrepreferences import GenrePreferences


class SelectGenreCD(cd.CallbackData, prefix="select_genre"):
    genre_id: int
    selected: bool


class SelectAllGenresCD(cd.CallbackData, prefix="select_all_genres"):
    selected: bool


class SetGenreCombinatorModeCD(cd.CallbackData, prefix="set_genre_combinator_mode"):
    require_all: bool


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

    @on.callback_query(SetGenreCombinatorModeCD.filter())
    async def on_set_genre_combinator_mode(
        self,
        callback_query: aiogram.types.CallbackQuery,
        callback_data: SetGenreCombinatorModeCD,
        session: async_sa.AsyncSession,
        current_user: models.User,
    ) -> None:
        preferences = GenrePreferences(session, current_user)

        if callback_data.require_all:
            await preferences.require_all_selected_genres()
            logger.info("Require all selected genres")
        else:
            await preferences.require_one_selected_genre()
            logger.info("Require one selected genre")
        await session.commit()

        await self._update_genre_combinator_selector(
            message=callback_query.message, genre_preferences=preferences
        )

        current_user.record_settings_update()
        await session.commit()

    @on.message(aiogram.F.text == CLOSE_SETTINGS_BTN)
    async def on_close(self, message: aiogram.types.Message):
        logger.debug("Closing settings")
        await self.wizard.back()

    @on.message.leave()
    async def on_leave(
        self,
        message: aiogram.types.Message,
        bot: aiogram.Bot,
        event_chat: aiogram.types.Chat,
        current_user: models.User,
        session: async_sa.AsyncSession,
    ) -> None:
        logger.debug("Leaving settings")

        genre_preferences = GenrePreferences(session, current_user)
        await self._close_genre_selector(
            bot=bot, chat_id=event_chat.id, genre_preferences=genre_preferences
        )
        await self._close_genre_combinator_selector(
            bot=bot,
            chat_id=event_chat.id,
            genre_preferences=genre_preferences,
        )

        await self.wizard.clear_data()

    async def _answer_with_genre_selector(
        self,
        message: aiogram.types.Message,
        genre_preferences: GenrePreferences,
    ) -> None:
        text = fmt.as_section(
            fmt.Underline("Genres"),
            "Select genre(s) that you interested in.",
        ).as_kwargs()
        reply_markup = await self._build_genre_selector_reply_markup(genre_preferences)
        sent_message = await message.answer(**text, reply_markup=reply_markup)
        await self._save_message_id(sent_message, "genre_selector_message_id")

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
        await self._answer_with_genre_combinator_selector(message, genre_preferences)

    async def _answer_with_settings_title(self, message: aiogram.types.Message):
        text = fmt.Bold("Settings").as_kwargs()
        reply_markup = (
            kb.ReplyKeyboardBuilder()
            .button(text=self.CLOSE_SETTINGS_BTN)
            .as_markup(resize_keyboard=True)
        )
        sent_message = await message.answer(**text, reply_markup=reply_markup)
        await self._save_message_id(sent_message, "title_message_id")

    async def _update_genre_selector(
        self,
        message: aiogram.types.Message,
        genre_preferences: GenrePreferences,
    ):
        reply_markup = await self._build_genre_selector_reply_markup(genre_preferences)
        await message.edit_reply_markup(reply_markup=reply_markup)

    async def _answer_with_genre_combinator_selector(
        self,
        message: aiogram.types.Message,
        genre_preferences: GenrePreferences,
    ) -> None:
        text = fmt.as_section(
            fmt.Underline("How to combine genres?"),
            "Require titles to have ",
            fmt.Italic("all"),
            " or ",
            fmt.Italic("at least 1"),
            " of the selected genres.",
        ).as_kwargs()
        reply_markup = await self._build_genre_combinator_selector_reply_markup(
            genre_preferences
        )

        sent_message = await message.answer(**text, reply_markup=reply_markup)
        await self._save_message_id(sent_message, "genre_combinator_message_id")

    @staticmethod
    async def _build_genre_combinator_selector_reply_markup(
        genre_preferences: GenrePreferences,
    ) -> aiogram.types.InlineKeyboardMarkup:
        builder = kb.InlineKeyboardBuilder()
        if await genre_preferences.check_all_selected_genres_are_required():
            builder.button(
                text="All", callback_data=SetGenreCombinatorModeCD(require_all=False)
            )
        else:
            builder.button(
                text="At Least 1",
                callback_data=SetGenreCombinatorModeCD(require_all=True),
            )
        return builder.as_markup()

    async def _update_genre_combinator_selector(
        self, message: aiogram.types.Message, genre_preferences: GenrePreferences
    ) -> None:
        reply_markup = await self._build_genre_combinator_selector_reply_markup(
            genre_preferences
        )
        await message.edit_reply_markup(reply_markup=reply_markup)

    async def _save_message_id(
        self, sent_message: aiogram.types.Message, key: str
    ) -> None:
        await self.wizard.update_data({key: sent_message.message_id})

    async def _close_genre_selector(
        self, bot: aiogram.Bot, chat_id: int, genre_preferences: GenrePreferences
    ) -> None:
        genres = (
            genre.name for genre in await genre_preferences.list_selected_genres()
        )
        text = fmt.as_section(
            fmt.Underline("Genres"),
            "Select genre(s) that you interested in.\n\n",
            fmt.as_marked_list(*genres, marker="✅ "),
        )

        try:
            message_id = await self.wizard.get_value("genre_selector_message_id")
        except KeyError:
            logger.error(
                "Failed to close the genre selector due to missing "
                '"genre_selector_message_id" key'
            )
            return

        with logger.catch(aiogram.exceptions.TelegramBadRequest, level="WARNING"):
            await bot.edit_message_text(
                chat_id=chat_id, message_id=message_id, **text.as_kwargs()
            )

    async def _close_genre_combinator_selector(
        self, bot: aiogram.Bot, chat_id: int, genre_preferences: GenrePreferences
    ) -> None:
        all_selected_genres_are_required = (
            await genre_preferences.check_all_selected_genres_are_required()
        )
        text = fmt.as_section(
            fmt.Underline("How to combine genres?"),
            "Require titles to have ",
            fmt.Italic("all"),
            " or ",
            fmt.Italic("at least 1"),
            " of the selected genres.",
            "\n\n",
            "✅ ",
            "All" if all_selected_genres_are_required else "At Least 1",
        )

        try:
            message_id = await self.wizard.get_value("genre_combinator_message_id")
        except KeyError:
            logger.error(
                "Failed to close the genre selector due to missing "
                '"genre_combinator_message_id" key'
            )
            return

        with logger.catch(aiogram.exceptions.TelegramBadRequest, level="WARNING"):
            await bot.edit_message_text(
                chat_id=chat_id, message_id=message_id, **text.as_kwargs()
            )
