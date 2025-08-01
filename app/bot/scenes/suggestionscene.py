import aiogram
import aiogram.exceptions
import aiogram.utils.formatting as fmt
from aiogram import F
from aiogram.fsm.scene import Scene, ScenesManager, on
from aiogram.utils.keyboard import InlineKeyboardBuilder
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import models
from app.core.services import suggestions as suggestion_service

SETTINGS_SCENE = "settings"


class SuggestionScene(Scene, state="suggestions"):
    """A scene where all suggestions are displayed.

    Each suggestion is displayed as a separate message with action buttons as
    an inline keyboard. After a user clicks on the button, the original message is
    edited to display the selected action and a new suggestion is sent.
    """

    @on.message.enter()
    async def enter_via_message(
        self, message: aiogram.types.Message, session: AsyncSession, user: models.User
    ) -> None:
        """Enter a scene via a message, delete the message and send a suggestion.

        :param message: An incoming message.
        :param session: An SQLAlchemy session for this event.
        :param user: A user who entered the scene.
        """

        logger.debug("Entering the suggestion scene via a message.")

        try:
            await message.delete()
        except aiogram.exceptions.TelegramAPIError as e:
            logger.warning(f"Failed to delete an incoming message. Reason: {e}")

        await self.send_suggestion(message.bot, session, user)

        logger.info("Entered the suggestion scene.")

    @on.callback_query.enter()
    async def enter_via_callback_query(
        self,
        callback_query: aiogram.types.CallbackQuery,
        session: AsyncSession,
        user: models.User,
    ) -> None:
        """Enter a scene via a callback query and send a suggestion. Expects that the
        original message, where the callback query was triggered, has been already
        deleted.

        :param callback_query: An incoming callback query.
        :param session: An SQLAlchemy session for this event.
        :param user: A user who entered the scene.
        """
        logger.debug("Entering the suggestion scene via a callback query.")

        await self.send_suggestion(callback_query.bot, session, user)

        logger.info("Entered the suggestion scene.")

    @on.callback_query(F.data == "new_suggestion")
    async def handle_new_suggestion_button_click(
        self,
        callback_query: aiogram.types.CallbackQuery,
        session: AsyncSession,
        user: models.User,
    ) -> None:
        """Handle a click on a new suggestion button and send a new suggestion
        after making the previous one non-interactive.

        :param callback_query: An incoming callback query.
        :param session: An SQLAlchemy session for this event.
        :param user: A user that needs a new suggestion.
        """

        logger.debug("Handling a new suggestion button click.")

        # Skip the old suggestion
        last_suggested_title_id = await self.wizard.get_value("last_suggested_title_id")
        await suggestion_service.skip_suggested_title(
            session, user, last_suggested_title_id
        )
        await session.commit()
        logger.info(f"Skipped the old suggestion with id={last_suggested_title_id}")

        # Make the old suggestion non-interactive
        try:
            await callback_query.message.edit_reply_markup()
        except aiogram.exceptions.TelegramAPIError as e:
            logger.warning(f"Failed to edit the old suggestion's message. Reason: {e}")
        else:
            logger.debug("Removed keyboard of the old suggestion's message")

        await self.send_suggestion(callback_query.bot, session, user)

    @on.callback_query(F.data == "settings")
    async def handle_settings_button_click(
        self, callback_query: aiogram.types.CallbackQuery, scenes: ScenesManager
    ) -> None:
        """Handle a click on settings button and go to settings.

        :param callback_query: An incoming callback query.
        :param scenes: A scene manager.
        """

        logger.debug("Handling settings button click.")
        await scenes.enter(SETTINGS_SCENE)
        logger.info("Went to settings")

    async def send_suggestion(
        self, bot: aiogram.Bot, session: AsyncSession, user: models.User
    ) -> None:
        """Send a new suggestion to a user or notify that no more suggestion available.

        :param bot: A bot that will be used to send a suggestion.
        :param session: An SQLAlchemy session.
        :param user: A user that needs the suggestion.
        """

        logger.debug("Sending a suggestion")

        if suggestion := await suggestion_service.suggest_title(session, user):
            logger.debug(f"{suggestion=}")
            text = fmt.as_list(
                fmt.Bold(
                    fmt.Underline(suggestion.title), f" ({suggestion.start_year})"
                ),
                "",
                fmt.as_key_value("Rating", f"⭐ {suggestion.rating:.1f}"),
                fmt.as_key_value(
                    "Genres",
                    ", ".join(
                        sorted(
                            genre.name
                            for genre in await suggestion.awaitable_attrs.genres
                        )
                    ),
                ),
                "",
                fmt.TextLink("IMDB", url=suggestion.imdb_url),
            )

            await self.wizard.update_data(last_suggested_title_id=suggestion.id)
        else:
            logger.debug("No suggestions")
            text = fmt.Text(
                "No new suggestions found. "
                "Try updating your filter settings or try again later."
            )
        reply_markup = (
            InlineKeyboardBuilder()
            .button(text="🔄 Next", callback_data="new_suggestion")
            .button(text="⚙ Settings", callback_data="settings")
            .adjust(1)
            .as_markup()
        )

        await bot.send_message(
            chat_id=user.id, **text.as_kwargs(), reply_markup=reply_markup
        )
        if suggestion:
            logger.info(f"Suggested a title with id={suggestion.id}.")
        else:
            logger.info("Notified that no suggestion is available.")
