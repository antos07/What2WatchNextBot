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
from app.bot.scenes.minimummovievotesselectorscene import (
    MinimumMovieVotesSelectorScene,
    MovieVotesButtonCD,
)
from app.core import models
from app.testing.mockedbot import MockedBot
from app.testing.scenes import BackSceneAction, FakeSceneWizard, RetakeSceneAction


@pytest.fixture()
def scene(scene_wizard: FakeSceneWizard) -> MinimumMovieVotesSelectorScene:
    return MinimumMovieVotesSelectorScene(cast(SceneWizard, scene_wizard))


async def test_exit_via_message(
    scene: MinimumMovieVotesSelectorScene,
    mocked_bot: MockedBot,
    fake_tg_message: Message,
) -> None:
    scene.cleanup = mock.AsyncMock()

    await scene.exit_via_message(fake_tg_message, mocked_bot)

    scene.cleanup.assert_awaited_once_with(mocked_bot)


async def test_handle_back_button_click(
    scene: MinimumMovieVotesSelectorScene,
    scene_wizard: FakeSceneWizard,
    fake_tg_callback_query: CallbackQuery,
) -> None:
    await scene.handle_back_button_click(fake_tg_callback_query)

    assert scene_wizard.scene_actions == [BackSceneAction()]


async def test_enter_via_callback_query(
    scene: MinimumMovieVotesSelectorScene,
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
                **fmt.Bold("Minimum Votes:").as_kwargs(),
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[]),
            )
        ],
    )
    scene.create_message_keyboard.assert_called_once_with(user)


def _create_unchecked_votes_button(votes: int) -> InlineKeyboardButton:
    return InlineKeyboardButton(
        text=f"{constants.UNCHECKED_CHECKBOX} {votes}",
        callback_data=MovieVotesButtonCD(votes=votes).pack(),
    )


def test_create_message_keyboard_6_point_5_selected(
    scene: MinimumMovieVotesSelectorScene,
    user: models.User,
) -> None:
    user.minimum_movie_votes = 10_000

    actual = scene.create_message_keyboard(user)
    expected = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                _create_unchecked_votes_button(1_000),
                InlineKeyboardButton(
                    text=f"{constants.CHECKED_CHECKBOX} 10000",
                    callback_data=MovieVotesButtonCD(votes=10_000).pack(),
                ),
                _create_unchecked_votes_button(50_000),
                _create_unchecked_votes_button(100_000),
                _create_unchecked_votes_button(200_000),
            ],
            [
                InlineKeyboardButton(
                    text=f"{constants.UNCHECKED_CHECKBOX} Any",
                    callback_data=MovieVotesButtonCD(votes=0).pack(),
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
    scene: MinimumMovieVotesSelectorScene,
    user: models.User,
) -> None:
    user.minimum_movie_votes = 0

    actual = scene.create_message_keyboard(user)
    expected = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                _create_unchecked_votes_button(1_000),
                _create_unchecked_votes_button(10_000),
                _create_unchecked_votes_button(50_000),
                _create_unchecked_votes_button(100_000),
                _create_unchecked_votes_button(200_000),
            ],
            [
                InlineKeyboardButton(
                    text=f"{constants.CHECKED_CHECKBOX} Any",
                    callback_data=MovieVotesButtonCD(votes=0).pack(),
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


async def test_handle_movie_votes_button_click(
    scene: MinimumMovieVotesSelectorScene,
    user: models.User,
    sa_async_session: AsyncSession,
    fake_tg_callback_query: CallbackQuery,
    scene_wizard: FakeSceneWizard,
) -> None:
    callback_data = MovieVotesButtonCD(votes=9)

    await scene.handle_movie_votes_button_click(
        callback_query=fake_tg_callback_query,
        user=user,
        session=sa_async_session,
        callback_data=callback_data,
    )

    await sa_async_session.refresh(user)
    assert user.minimum_movie_votes == 9
    assert scene_wizard.scene_actions == [
        RetakeSceneAction(data={"_with_history": False})
    ]
