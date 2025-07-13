import operator

import aiogram
from aiogram import F
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.scene import on
from aiogram.utils import formatting as fmt
from aiogram.utils.keyboard import InlineKeyboardBuilder
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot import constants
from app.core import models
from app.core.services import genre as genre_service

from ._autocleanupscene import AutoCleanupScene


class GenreButtonCD(CallbackData, prefix="genre"):
    genre_id: int
    selected: bool


class GenreSelectorScene(AutoCleanupScene, state="genre"):
    @on.callback_query.enter()
    async def enter_via_callback_query(
        self,
        callback_query: aiogram.types.CallbackQuery,
        user: models.User,
        session: AsyncSession,
    ) -> None:
        logger.debug("Entering the genre selector via a callback query.")

        await callback_query.message.edit_text(
            **self.construct_message_text().as_kwargs(),
            reply_markup=await self.construct_message_keyboard(user, session),
        )

        logger.info("Entered the genre selector")

    @on.callback_query(F.data == constants.BACK_BUTTON_CD)
    async def handle_back_button_click(
        self, callback_query: aiogram.types.CallbackQuery
    ) -> None:
        """Handle the back button click and go back to the previous scene."""

        logger.debug("Handling the back button click.")
        await self.wizard.back()
        logger.info("Handled the back button click. Went back to settings.")

    @on.callback_query(GenreButtonCD.filter())
    async def handle_genre_button_click(
        self,
        callback_query: aiogram.types.CallbackQuery,
        user: models.User,
        session: AsyncSession,
        callback_data: GenreButtonCD,
    ) -> None:
        """Handle a user click on a genre button."""

        logger.debug(
            f"User selected: genre_id={callback_data.genre_id!r}, "
            f"selected={callback_data.selected!r}"
        )

        genre = await genre_service.get_by_id(session, callback_data.genre_id)
        if callback_data.selected:
            await user.select_genre(genre)
        else:
            await user.deselect_genre(genre)
        await session.commit()
        logger.info(
            f"Genre id={callback_data.genre_id!r}: selected={callback_data.selected!r}."
        )

        # Update the message
        await self.wizard.retake(_with_history=False)

    @staticmethod
    def construct_message_text() -> fmt.Text:
        return fmt.Bold("Genres:")

    @staticmethod
    async def construct_message_keyboard(
        user: models.User, session: AsyncSession
    ) -> aiogram.types.InlineKeyboardMarkup:
        """Construct a message keyboard for a user.

        :param user: A user who needs the keyboard.
        :param session: An SQLAlchemy session.
        """

        all_genres = await genre_service.list_all(session)
        all_genres.sort(key=operator.attrgetter("name"))
        selected_genres = await user.awaitable_attrs.selected_genres

        genre_button_builder = InlineKeyboardBuilder()
        for genre in all_genres:
            selected = genre in selected_genres
            checkbox = (
                constants.CHECKED_CHECKBOX if selected else constants.UNCHECKED_CHECKBOX
            )
            name = genre.name.capitalize()
            text = f"{checkbox} {name}"

            genre_button_builder.button(
                text=text,
                callback_data=GenreButtonCD(genre_id=genre.id, selected=not selected),
            )

        return (
            InlineKeyboardBuilder()
            .attach(genre_button_builder.adjust(3))
            .attach(
                InlineKeyboardBuilder().button(
                    text=constants.BACK_BUTTON_TEXT,
                    callback_data=constants.BACK_BUTTON_CD,
                )
            )
            .as_markup()
        )
