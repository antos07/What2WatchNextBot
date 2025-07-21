import aiogram.filters
from aiogram import F
from aiogram.fsm.scene import ScenesManager, on
from aiogram.utils import formatting as fmt
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.bot.scenes._autocleanupscene import AutoCleanupScene
from app.bot.scenes.genreselectorscene import GenreSelectorScene
from app.bot.scenes.minimummovieratingselectorscene import (
    MinimumMovieRatingSelectorScene,
)
from app.bot.scenes.minimummovievotesselectorscene import MinimumMovieVotesSelectorScene
from app.bot.scenes.suggestionscene import SuggestionScene
from app.bot.scenes.titletypeselectorscene import TitleTypeSelectorScene
from app.core import models
from app.logging import logger


class SettingsScene(AutoCleanupScene, state="settings"):
    """This is the scene with the main page of a user's settings."""

    @on.message.enter()
    async def enter_via_message(
        self, message: aiogram.types.Message, user: models.User
    ) -> None:
        """This method is called when the user enters the scene via a message."""

        logger.debug("Entering settings via a message.")

        await self.register_for_cleanup(message)

        sent_message = await message.answer(
            **(await self.construct_settings_text(user)).as_kwargs(),
            reply_markup=self.construct_settings_keyboard(),
        )
        await self.register_for_cleanup(sent_message)

        logger.info("Entered settings")

    @on.callback_query.enter()
    async def enter_via_callback_query(
        self, callback_query: aiogram.types.CallbackQuery, user: models.User
    ) -> None:
        """This method is called when the user enters the scene via a message."""

        logger.debug("Entering settings via a callback query.")

        await callback_query.message.edit_text(
            **(await self.construct_settings_text(user)).as_kwargs(),
            reply_markup=self.construct_settings_keyboard(),
        )

        logger.info("Entered settings")

    @on.message.exit()
    async def exit_via_message(
        self, message: aiogram.types.Message, bot: aiogram.Bot
    ) -> None:
        """This method is called when the user exits the scene via a message.
        It should clean up the screen from any leftover messages."""

        logger.debug("Exiting settings via a message.")

        await self.cleanup(bot)

        logger.info("Exited settings")

    @on.callback_query(F.data == "title_types")
    async def handle_title_types_button_click(
        self, callback_query: aiogram.types.CallbackQuery
    ) -> None:
        """This method is called when the user clicks the "Title Types"
        button in the settings."""

        logger.debug("Handling title types button click.")

        await self.wizard.goto(TitleTypeSelectorScene)

        logger.info("Handled title types button click. Going to title type selector.")

    @on.callback_query(F.data == "genres")
    async def handle_genres_button_click(
        self, callback_query: aiogram.types.CallbackQuery
    ) -> None:
        """This method is called when the user clicks the "Genres"
        button in the settings."""

        logger.debug("Handling genres button click.")

        await self.wizard.goto(GenreSelectorScene)

        logger.info("Handled genres button click. Going to the genre selector.")

    @on.callback_query(F.data == "minimum_rating")
    async def handle_minimum_rating_button_click(
        self, callback_query: aiogram.types.CallbackQuery
    ) -> None:
        """This method is called when the user clicks the "Minimum Rating"
        button in the settings."""

        logger.debug("Handling minimum rating button click.")

        await self.wizard.goto(MinimumMovieRatingSelectorScene)

        logger.info(
            "Handled minimum rating button click. Going to the minimum rating selector."
        )

    @on.callback_query(F.data == "minimum_votes")
    async def handle_minimum_votes_button_click(
        self, callback_query: aiogram.types.CallbackQuery
    ) -> None:
        """This method is called when the user clicks the "Minimum Votes"
        button in the settings."""

        logger.debug("Handling minimum votes button click.")

        await self.wizard.goto(MinimumMovieVotesSelectorScene)

        logger.info(
            "Handled minimum votes button click. Going to the minimum votes selector."
        )

    @on.callback_query(F.data == "close")
    async def handle_close_button_click(
        self, callback_query: aiogram.types.CallbackQuery, scenes: ScenesManager
    ) -> None:
        """This method is called when the user clicks the "Close" button."""

        logger.debug("Handling close button click.")

        # We want to delete the message even if we got here via a callback query.
        await self.register_for_cleanup(callback_query.message)

        await self.cleanup(callback_query.bot)
        logger.debug("Cleaned up settings")

        await scenes.enter(SuggestionScene)
        logger.info("Went to suggestions")

    @staticmethod
    async def construct_settings_text(user: models.User) -> fmt.Text:
        """Construct the text to be shown to the user in this scene.

        :param user: The user object that contains the settings.
        :return: The text to be shown to the user.
        """

        selected_title_types = await user.awaitable_attrs.selected_title_types
        selected_title_types = ", ".join(sorted(tt.name for tt in selected_title_types))
        selected_genres = await user.awaitable_attrs.selected_genres
        selected_genres = ", ".join(sorted(genre.name for genre in selected_genres))
        selected_genres += f" ({'all' if user.requires_all_selected_genres else 'any'})"
        return fmt.as_section(
            fmt.Bold("⚙ ", fmt.Underline("Settings")),
            "\n",
            fmt.as_list(
                fmt.as_key_value("Title Types", selected_title_types),
                fmt.as_key_value("Genres", selected_genres),
                fmt.as_key_value("Minimum Rating", user.minimum_movie_rating or "any"),
                fmt.as_key_value("Minimum Votes", user.minimum_movie_votes or "any"),
            ),
        )

    @staticmethod
    def construct_settings_keyboard() -> aiogram.types.InlineKeyboardMarkup:
        """Construct the keyboard to be shown to the user in this scene.

        :return: The keyboard to be shown to the user.
        """

        return (
            InlineKeyboardBuilder()
            .button(text="Title Types", callback_data="title_types")
            .button(text="Genres", callback_data="genres")
            .button(text="Minimum Rating", callback_data="minimum_rating")
            .button(text="Minimum Votes", callback_data="minimum_votes")
            .button(text="❌ Close", callback_data="close")
            .adjust(2, 2, 1)
            .as_markup()
        )
