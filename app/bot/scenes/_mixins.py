import aiogram
from aiogram import F
from aiogram.fsm.scene import SceneWizard, on
from loguru import logger

from app.bot import constants


class HandleBackButtonClickMixin:
    """A mixin that provides the handle_back_button_click handler that triggers on
    callback queries with data ``constants.BACK_BUTTON_CD`` and a method for
    creating a back button."""

    wizard: SceneWizard

    @on.callback_query(F.data == constants.BACK_BUTTON_CD)
    async def handle_back_button_click(
        self, callback_query: aiogram.types.CallbackQuery
    ) -> None:
        logger.debug("Handling a back button click.")

        await self.wizard.back()

        new_state = await self.wizard.state.get_state()
        logger.info(f"Handled a back button click. Went back to state: {new_state!r}.")

    @staticmethod
    def get_back_button() -> aiogram.types.InlineKeyboardButton:
        """Create a back button."""

        return aiogram.types.InlineKeyboardButton(
            text=constants.BACK_BUTTON_TEXT,
            callback_data=constants.BACK_BUTTON_CD,
        )
