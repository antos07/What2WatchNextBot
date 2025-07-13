import aiogram
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.scene import on
from aiogram.utils import formatting as fmt
from aiogram.utils.keyboard import InlineKeyboardBuilder
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import models

from ..utils import get_checkbox
from ._autocleanupscene import AutoCleanupScene
from ._mixins import HandleBackButtonClickMixin


class MovieVotesButtonCD(CallbackData, prefix="movie_votes"):
    votes: int


class MinimumMovieVotesSelectorScene(
    AutoCleanupScene, HandleBackButtonClickMixin, state="movie_votes"
):
    """A scene where a user is presented with a selection of possible
    movie votes filters.
    """

    @on.callback_query.enter()
    async def enter_via_callback_query(
        self, callback_query: aiogram.types.CallbackQuery, user: models.User
    ) -> None:
        """Prepare the scene when a user enters it via a callback query.

        :param callback_query: A callback query that triggered the handler.
        :param user: The user who entered the scene.
        """

        logger.debug("Entering the minimum movie votes selector via a callback query.")

        await callback_query.message.edit_text(
            **self.create_message_text().as_kwargs(),
            reply_markup=self.create_message_keyboard(user),
        )

        logger.info("Entered the minimum movie votes selector.")

    @on.callback_query(MovieVotesButtonCD.filter())
    async def handle_movie_votes_button_click(
        self,
        callback_query: aiogram.types.CallbackQuery,
        user: models.User,
        session: AsyncSession,
        callback_data: MovieVotesButtonCD,
    ) -> None:
        """Handle a user clicking on a movie votes button and update the user's
        minimum movie votes.

        :param callback_query: A callback query that triggered the handler.
        :param user: The user who clicked the button.
        :param session: An SQLAlchemy session for this event.
        :param callback_data: Parsed callback data.
        """

        logger.debug("Handling a movie votes button click.")

        user.minimum_movie_votes = callback_data.votes
        await session.commit()
        logger.info(f"Set {user.minimum_movie_votes=}")

        await self.wizard.retake(_with_history=False)

    @staticmethod
    def create_message_text() -> fmt.Text:
        return fmt.Bold("Minimum Votes:")

    def create_message_keyboard(
        self,
        user: models.User,
    ) -> aiogram.types.InlineKeyboardMarkup:
        possible_votes = [1_000, 10_000, 50_000, 100_000, 200_000]
        votes_buttons_builder = InlineKeyboardBuilder()
        any_option_selected = False

        logger.debug(f"{user.minimum_movie_votes=}")

        for votes in possible_votes:
            selected = user.minimum_movie_votes == votes
            checkbox = get_checkbox(selected)
            text = f"{checkbox} {votes}"

            if selected:
                any_option_selected = True

            votes_buttons_builder.button(
                text=text,
                callback_data=MovieVotesButtonCD(votes=votes),
            )

        # Special case - any votes (min votes is 0)
        selected = user.minimum_movie_votes == 0
        votes_buttons_builder.button(
            text=f"{get_checkbox(selected)} Any",
            callback_data=MovieVotesButtonCD(votes=0),
        )
        if selected:
            any_option_selected = True

        if not any_option_selected:
            logger.warning(f"No option selected. {user.minimum_movie_votes=}")

        votes_buttons_builder.adjust(len(possible_votes), 1)

        return (
            InlineKeyboardBuilder()
            .attach(votes_buttons_builder)
            .row(self.get_back_button())
            .as_markup()
        )
