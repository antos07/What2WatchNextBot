import aiogram.exceptions
import aiogram.filters
from aiogram.fsm.scene import Scene, on
from aiogram.utils import formatting as fmt
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.core import models


class SettingsScene(Scene, state="settings"):
    """This is the scene with the main page of a user's settings."""

    @on.message.enter()
    async def enter_via_message(
        self, message: aiogram.types.Message, user: models.User
    ) -> None:
        """This method is called when the user enters the scene via a message."""

        sent_message = await message.answer(
            **(await self.construct_settings_text(user)).as_kwargs(),
            reply_markup=self.construct_settings_keyboard(),
        )
        await self.wizard.update_data(sent_message_id=sent_message.message_id)

    @on.message.exit()
    async def exit_via_message(
        self, message: aiogram.types.Message, bot: aiogram.Bot
    ) -> None:
        """This method is called when the user exits the scene via a message.
        It should clean up the screen from any leftover messages."""
        sent_message_id: int = await self.wizard.get_value("sent_message_id")
        try:
            await bot.delete_message(
                chat_id=message.chat.id, message_id=sent_message_id
            )
        except aiogram.exceptions.TelegramBadRequest:
            pass

    @staticmethod
    async def construct_settings_text(user: models.User) -> fmt.Text:
        """Construct the text to be shown to the user in this scene.

        :param user: The user object that contains the settings.
        :return: The text to be shown to the user.
        """

        selected_title_types = await user.awaitable_attrs.selected_title_types
        selected_title_types = ", ".join(tt.name for tt in selected_title_types)
        selected_genres = await user.awaitable_attrs.selected_genres
        selected_genres = ", ".join(genre.name for genre in selected_genres)
        return fmt.as_section(
            fmt.Bold("⚙ ", fmt.Underline("Settings")),
            "\n",
            fmt.as_list(
                fmt.as_key_value("Title Types", selected_title_types),
                fmt.as_key_value("Genres", selected_genres),
                fmt.as_key_value("Minimum Rating", user.minimum_movie_rating),
                fmt.as_key_value("Minimum Votes", user.minimum_movie_votes),
            ),
        )

    @staticmethod
    def construct_settings_keyboard() -> aiogram.types.InlineKeyboardMarkup:
        """Construct the keyboard to be shown to the user in this scene.

        :return: The keyboard to be shown to the user.
        """

        return InlineKeyboardBuilder().as_markup()
