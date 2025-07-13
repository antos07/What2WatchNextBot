from typing import cast

import pytest
from aiogram.fsm.scene import SceneWizard
from aiogram.methods import EditMessageText
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from aiogram.utils import formatting as fmt
from sqlalchemy.ext.asyncio import AsyncSession
from testfixtures import compare, mock

from app.bot import constants
from app.bot.scenes.minimummovieratingselectorscene import (
    MinimumMovieRatingSelectorScene,
    MovieRatingButtonCD,
)
from app.core import models
from app.testing.mockedbot import MockedBot
from app.testing.scenes import BackSceneAction, FakeSceneWizard, RetakeSceneAction


@pytest.fixture()
def scene(scene_wizard: FakeSceneWizard) -> MinimumMovieRatingSelectorScene:
    return MinimumMovieRatingSelectorScene(cast(SceneWizard, scene_wizard))


async def test_exit_via_message(
    scene: MinimumMovieRatingSelectorScene,
    mocked_bot: MockedBot,
    fake_tg_message: Message,
) -> None:
    scene.cleanup = mock.AsyncMock()

    await scene.exit_via_message(fake_tg_message, mocked_bot)

    scene.cleanup.assert_awaited_once_with(mocked_bot)


async def test_handle_back_button_click(
    scene: MinimumMovieRatingSelectorScene,
    scene_wizard: FakeSceneWizard,
    fake_tg_callback_query: CallbackQuery,
) -> None:
    await scene.handle_back_button_click(fake_tg_callback_query)

    assert scene_wizard.scene_actions == [BackSceneAction()]


async def test_enter_via_callback_query(
    scene: MinimumMovieRatingSelectorScene,
    fake_tg_callback_query: CallbackQuery,
    fake_tg_message: Message,
    mocked_bot: MockedBot,
    user: models.User,
) -> None:
    scene.create_message_keyboard = mock.Mock(
        return_value=InlineKeyboardMarkup(inline_keyboard=[])
    )

    await scene.enter_via_callback_query(fake_tg_callback_query, user)

    compare(
        mocked_bot.calls,
        [
            EditMessageText(
                chat_id=fake_tg_message.chat.id,
                message_id=fake_tg_message.message_id,
                **fmt.Bold("Minimum Rating:").as_kwargs(),
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[]),
            )
        ],
    )
    scene.create_message_keyboard.assert_called_once_with(user)


def _create_unchecked_rating_button(rating: float) -> InlineKeyboardButton:
    return InlineKeyboardButton(
        text=f"{constants.UNCHECKED_CHECKBOX} {rating}",
        callback_data=MovieRatingButtonCD(rating=rating).pack(),
    )


def test_create_message_keyboard_6_point_5_selected(
    scene: MinimumMovieRatingSelectorScene,
    user: models.User,
) -> None:
    user.minimum_movie_rating = 6.5

    actual = scene.create_message_keyboard(user)
    expected = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                _create_unchecked_rating_button(9),
                _create_unchecked_rating_button(9.5),
            ],
            [
                _create_unchecked_rating_button(8),
                _create_unchecked_rating_button(8.5),
            ],
            [
                _create_unchecked_rating_button(7),
                _create_unchecked_rating_button(7.5),
            ],
            [
                _create_unchecked_rating_button(6),
                InlineKeyboardButton(
                    text=f"{constants.CHECKED_CHECKBOX} 6.5",
                    callback_data=MovieRatingButtonCD(rating=6.5).pack(),
                ),
            ],
            [
                _create_unchecked_rating_button(5),
                _create_unchecked_rating_button(5.5),
            ],
            [
                InlineKeyboardButton(
                    text=f"{constants.UNCHECKED_CHECKBOX} Any",
                    callback_data=MovieRatingButtonCD(rating=0).pack(),
                )
            ],
            [
                InlineKeyboardButton(
                    text=constants.BACK_BUTTON_TEXT,
                    callback_data=constants.BACK_BUTTON_CD,
                )
            ],
        ]
    )

    assert actual == expected


def test_create_message_keyboard_any_selected(
    scene: MinimumMovieRatingSelectorScene,
    user: models.User,
) -> None:
    user.minimum_movie_rating = 0

    actual = scene.create_message_keyboard(user)
    expected = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                _create_unchecked_rating_button(9),
                _create_unchecked_rating_button(9.5),
            ],
            [
                _create_unchecked_rating_button(8),
                _create_unchecked_rating_button(8.5),
            ],
            [
                _create_unchecked_rating_button(7),
                _create_unchecked_rating_button(7.5),
            ],
            [
                _create_unchecked_rating_button(6),
                _create_unchecked_rating_button(6.5),
            ],
            [
                _create_unchecked_rating_button(5),
                _create_unchecked_rating_button(5.5),
            ],
            [
                InlineKeyboardButton(
                    text=f"{constants.CHECKED_CHECKBOX} Any",
                    callback_data=MovieRatingButtonCD(rating=0).pack(),
                )
            ],
            [
                InlineKeyboardButton(
                    text=constants.BACK_BUTTON_TEXT,
                    callback_data=constants.BACK_BUTTON_CD,
                )
            ],
        ]
    )

    assert actual == expected


async def test_handle_movie_rating_button_click(
    scene: MinimumMovieRatingSelectorScene,
    user: models.User,
    sa_async_session: AsyncSession,
    fake_tg_callback_query: CallbackQuery,
    scene_wizard: FakeSceneWizard,
) -> None:
    callback_data = MovieRatingButtonCD(rating=9)

    await scene.handle_movie_rating_button_click(
        callback_query=fake_tg_callback_query,
        user=user,
        session=sa_async_session,
        callback_data=callback_data,
    )

    await sa_async_session.refresh(user)
    assert user.minimum_movie_rating == 9
    assert scene_wizard.scene_actions == [
        RetakeSceneAction(data={"_with_history": False})
    ]
