import aiogram.types
import aiogram.utils.formatting as fmt
import aiogram.utils.keyboard as kb
import sqlalchemy.ext.asyncio as async_sa
from aiogram.fsm.scene import Scene, on
from loguru import logger

from what2watchnextbot import models, suggestions
from what2watchnextbot.routers.main.scenes.titlefiltersscene import TitleFilterScene


class SuggestionScene(Scene, state="suggestions"):
    SKIP_BUTTON = "🔀 Maybe Later"
    WATCHED_BUTTON = "✔ Already Watched"
    UNINTERESTED_BUTTON = "❌ Uninterested"
    SETTINGS_BUTTON = "⚙ Settings"
    TRY_AGAIN_BUTTON = "🔁 Try Again"

    @on.message.enter()
    @on.message(aiogram.F.text == SKIP_BUTTON)
    @on.message(aiogram.F.text == TRY_AGAIN_BUTTON)
    async def on_new_suggestion_request(
        self,
        message: aiogram.types.Message,
        session: async_sa.AsyncSession,
        current_user: models.User,
    ) -> None:
        logger.debug("Handling new suggestion request")

        if current_user.last_settings_update_at is None:
            logger.debug(f"Entering for the 1st time - going to {TitleFilterScene}")
            await self.wizard.goto(TitleFilterScene)
        else:
            logger.debug("Reentering - displaying suggestion")
            await self._answer_with_suggestion(
                message=message,
                session=session,
                current_user=current_user,
            )

    @on.message(aiogram.F.text == WATCHED_BUTTON)
    async def on_watched_title(
        self,
        message: aiogram.types.Message,
        session: async_sa.AsyncSession,
        current_user: models.User,
    ) -> None:
        logger.debug("Handling watched title")

        title_id: int = await self.wizard.get_value("last_title_id")
        logger.debug(f"{title_id=}")
        if title_id is None:
            logger.error('"last_title_id" was not found in the current state')
            await self._answer_with_suggestion(
                message=message, session=session, current_user=current_user
            )
            return

        title = await session.get_one(models.Title, (title_id,))
        logger.debug("title={}", title)

        watched_titles = await current_user.awaitable_attrs.watched_titles
        watched_titles.add(title)
        await session.commit()
        logger.info(f"Marked title id={title_id} as watched")

        await self._answer_with_suggestion(
            message=message,
            session=session,
            current_user=current_user,
        )

    @on.message(aiogram.F.text == UNINTERESTED_BUTTON)
    async def on_ignored_title(
        self,
        message: aiogram.types.Message,
        session: async_sa.AsyncSession,
        current_user: models.User,
    ) -> None:
        logger.debug("Handling ignored title")

        title_id: int = await self.wizard.get_value("last_title_id")
        logger.debug(f"{title_id=}")
        if title_id is None:
            logger.error('"last_title_id" was not found in the current state')
            await self._answer_with_suggestion(
                message=message, session=session, current_user=current_user
            )
            return

        title = await session.get_one(models.Title, (title_id,))
        logger.debug("title={}", title)

        ignored_titles = await current_user.awaitable_attrs.ignored_titles
        ignored_titles.add(title)
        await session.commit()
        logger.info(f"Marked title id={title_id} as ignored")

        await self._answer_with_suggestion(
            message=message,
            session=session,
            current_user=current_user,
        )

    @on.message(aiogram.F.text == SETTINGS_BUTTON)
    async def on_open_settings(self, message: aiogram.types.Message) -> None:
        logger.debug("Opening settings")
        await self.wizard.goto(TitleFilterScene)

    async def _answer_with_suggestion(
        self,
        message: aiogram.types.Message,
        session: async_sa.AsyncSession,
        current_user: models.User,
    ) -> None:
        title = await suggestions.suggest(session=session, user=current_user)

        if not title:
            logger.info("No new suggestions")
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
            text = fmt.as_list(
                fmt.Bold(fmt.Underline(title.title), f" ({title.start_year})"),
                "",
                fmt.as_key_value("Rating", f"⭐ {title.rating:.1f}"),
                fmt.as_key_value(
                    "Genres",
                    ", ".join(
                        sorted(
                            genre.name for genre in await title.awaitable_attrs.genres
                        )
                    ),
                ),
                "",
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

            # Save the title ID to be able to use it later
            await self.wizard.update_data(last_title_id=title.id)

        text = text.as_kwargs()
        reply_markup = reply_markup.as_markup(resize_keyboard=True)
        await message.answer(**text, reply_markup=reply_markup)
        logger.info(f"Displayed suggested title id={title.id if title else None}")
