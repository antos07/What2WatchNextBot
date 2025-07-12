import aiogram
import sqlalchemy.ext.asyncio as sa_async
from aiogram import F
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.scene import on
from aiogram.utils import formatting as fmt
from aiogram.utils.keyboard import InlineKeyboardBuilder
from loguru import logger

from app.bot import constants
from app.bot.scenes._autocleanupscene import AutoCleanupScene
from app.core import models
from app.core.services import title_type as title_type_service


class TitleTypeButton(CallbackData, prefix="title_type"):
    title_type_id: int
    selected: bool


class TitleTypeSelectorScene(AutoCleanupScene, state="title_type_selector"):
    @on.callback_query.enter()
    async def enter_via_callback_query(
        self,
        callback_query: aiogram.types.CallbackQuery,
        user: models.User,
        session: sa_async.AsyncSession,
    ) -> None:
        logger.debug("Entering the title type selector via a callback query.")

        await callback_query.message.edit_text(
            **self.construct_message_text().as_kwargs(),
            reply_markup=await self.construct_message_keyboard(user, session),
        )

        logger.info("Entered the title type selector")

    @on.callback_query(F.data == constants.BACK_BUTTON_CD)
    async def handle_back_button_click(
        self, callback_query: aiogram.types.CallbackQuery
    ) -> None:
        logger.debug("Handling the back button click.")

        await self.wizard.back()

        logger.info("Handled the back button click. Going back to settings.")

    @staticmethod
    def construct_message_text() -> fmt.Text:
        """Construct the text to be shown to the user in this scene.

        :return: The text to be shown to the user.
        """

        return fmt.Bold("Title Types:")

    @staticmethod
    async def construct_message_keyboard(
        user: models.User, session: sa_async.AsyncSession
    ) -> aiogram.types.InlineKeyboardMarkup:
        """Construct the keyboard to be shown to the user in this scene.

        :param user: The user object that contains the settings.
        :param session: SQLAlchemy async session.
        :return: The keyboard to be shown to the user.
        """

        all_title_types = await title_type_service.list_all(session)
        selected_title_types: set[
            models.TitleType
        ] = await user.awaitable_attrs.selected_title_types

        # Construct a button for each title type and put them in a single row.
        # This should be okay because there won't be many.
        row: list[aiogram.types.InlineKeyboardButton] = []
        for title_type in all_title_types:
            selected = title_type in selected_title_types
            checkbox = (
                constants.CHECKED_CHECKBOX if selected else constants.UNCHECKED_CHECKBOX
            )
            name = title_type.name.capitalize()

            button = aiogram.types.InlineKeyboardButton(
                text=f"{checkbox} {name}",
                callback_data=TitleTypeButton(
                    title_type_id=title_type.id, selected=not selected
                ).pack(),
            )
            row.append(button)

        return (
            InlineKeyboardBuilder()
            .row(*row)
            .button(
                text=constants.BACK_BUTTON_TEXT, callback_data=constants.BACK_BUTTON_CD
            )
            .adjust(len(row), 1)
            .as_markup()
        )
