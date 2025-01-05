import aiogram.types
import aiogram.utils.formatting as fmt
import aiogram.utils.keyboard as kb
import sqlalchemy.ext.asyncio as async_sa
from aiogram.fsm.scene import Scene, on

from what2watchnextbot import models, suggestions
from what2watchnextbot.routers.main.scenes.titlefiltersscene import TitleFilterScene


class SuggestionScene(Scene, state="suggestions"):
    SKIP_BUTTON = "Maybe Later"
    WATCHED_BUTTON = "Already Watched"
    UNINTERESTED_BUTTON = "Uninterested"
    SETTINGS_BUTTON = "Settings"
    TRY_AGAIN_BUTTON = "Try Again"

    @on.message.enter()
    @on.message(aiogram.F.text == SKIP_BUTTON)
    @on.message(aiogram.F.text == TRY_AGAIN_BUTTON)
    @on.message(aiogram.F.text == UNINTERESTED_BUTTON)
    @on.message(aiogram.F.text == WATCHED_BUTTON)
    async def on_new_suggestion_request(
        self,
        message: aiogram.types.Message,
        session: async_sa.AsyncSession,
        current_user: models.User,
    ) -> None:
        if current_user.last_settings_update_at is None:
            await self.wizard.goto(TitleFilterScene)
        else:
            await self._answer_with_suggestion(
                message=message,
                session=session,
                current_user=current_user,
            )

    @on.message(aiogram.F.text == SETTINGS_BUTTON)
    async def on_open_settings(self, message: aiogram.types.Message) -> None:
        await self.wizard.goto(TitleFilterScene)

    async def _answer_with_suggestion(
        self,
        message: aiogram.types.Message,
        session: async_sa.AsyncSession,
        current_user: models.User,
    ) -> None:
        title = await suggestions.suggest(session=session, user=current_user)

        if not title:
            text = fmt.Text(
                "No new suggestions found. Try updating your filter settings"
            )
            reply_markup = (
                kb.ReplyKeyboardBuilder()
                .button(text=self.TRY_AGAIN_BUTTON)
                .button(text=self.SETTINGS_BUTTON)
                .adjust(1, 1)
            )
        else:
            text = fmt.as_section(
                fmt.Bold(title.title),
                "\n",
                fmt.TextLink("IMDB", url=title.imdb_url),
            )
            reply_markup = (
                kb.ReplyKeyboardBuilder()
                .button(text=self.SKIP_BUTTON)
                .button(text=self.UNINTERESTED_BUTTON)
                .button(text=self.WATCHED_BUTTON)
                .button(text=self.SETTINGS_BUTTON)
                .adjust(3, 1)
            )

        text = text.as_kwargs()
        reply_markup = reply_markup.as_markup(resize_keyboard=True)
        await message.answer(**text, reply_markup=reply_markup)
