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


class MovieRatingButtonCD(CallbackData, prefix="movie_rating"):
    rating: float


class MinimumMovieRatingSelectorScene(
    AutoCleanupScene, HandleBackButtonClickMixin, state="movie_rating"
):
    """A scene where a user is presented with a selection of possible
    movie rating filters.
    """

    @on.callback_query.enter()
    async def enter_via_callback_query(
        self, callback_query: aiogram.types.CallbackQuery, user: models.User
    ) -> None:
        """Prepare the scene when a user enters it via a callback query.

        :param callback_query: A callback query that triggered the handler.
        :param user: The user who entered the scene.
        """

        logger.debug("Entering the minimum movie rating selector via a callback query.")

        await callback_query.message.edit_text(
            **self.create_message_text().as_kwargs(),
            reply_markup=self.create_message_keyboard(user),
        )

        logger.info("Entered the minimum movie rating selector.")

    @on.callback_query(MovieRatingButtonCD.filter())
    async def handle_movie_rating_button_click(
        self,
        callback_query: aiogram.types.CallbackQuery,
        user: models.User,
        session: AsyncSession,
        callback_data: MovieRatingButtonCD,
    ) -> None:
        """Handle a user clicking on a movie rating button and update the user's
        minimum movie rating.

        :param callback_query: A callback query that triggered the handler.
        :param user: The user who clicked the button.
        :param session: An SQLAlchemy session for this event.
        :param callback_data: Parsed callback data.
        """

        logger.debug("Handling a movie rating button click.")

        if user.minimum_movie_rating == callback_data.rating:
            logger.info("Same value. No update needed")
            await callback_query.answer()
            return

        user.minimum_movie_rating = callback_data.rating
        await session.commit()
        logger.info(f"Set {user.minimum_movie_rating=}")

        await self.wizard.retake(_with_history=False)

    @staticmethod
    def create_message_text() -> fmt.Text:
        return fmt.Bold("Minimum Rating:")

    def create_message_keyboard(
        self,
        user: models.User,
    ) -> aiogram.types.InlineKeyboardMarkup:
        possible_ratings = [9, 9.5, 8, 8.5, 7, 7.5, 6, 6.5, 5, 5.5]
        rating_buttons_builder = InlineKeyboardBuilder()
        any_option_selected = False

        logger.debug(f"{user.minimum_movie_rating=}")

        for rating in possible_ratings:
            selected = user.minimum_movie_rating == rating
            checkbox = get_checkbox(selected)
            text = f"{checkbox} {rating}"

            if selected:
                any_option_selected = True

            rating_buttons_builder.button(
                text=text,
                callback_data=MovieRatingButtonCD(rating=rating),
            )

        # Special case - any rating (min rating is 0)
        selected = user.minimum_movie_rating == 0
        rating_buttons_builder.button(
            text=f"{get_checkbox(selected)} Any",
            callback_data=MovieRatingButtonCD(rating=0),
        )
        if selected:
            any_option_selected = True

        if not any_option_selected:
            logger.warning(f"No option selected. {user.minimum_movie_votes=}")

        # Expected shape:
        # 9 9.5
        # 8 8.5
        # ...
        # Any
        button_shape = [2] * (len(possible_ratings) // 2) + [1]
        rating_buttons_builder.adjust(*button_shape)

        return (
            InlineKeyboardBuilder()
            .attach(rating_buttons_builder)
            .row(self.get_back_button())
            .as_markup()
        )
