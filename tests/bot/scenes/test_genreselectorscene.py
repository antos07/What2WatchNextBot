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
from testfixtures import compare

from app.bot import constants
from app.bot.scenes import GenreSelectorScene
from app.bot.scenes.genreselectorscene import GenreButtonCD
from app.core import models
from app.testing.mockedbot import MockedBot
from app.testing.scenes import BackSceneAction, FakeSceneWizard, RetakeSceneAction
from app.utils import awaitable


@pytest.fixture()
def scene(scene_wizard: FakeSceneWizard) -> GenreSelectorScene:
    return GenreSelectorScene(cast(SceneWizard, scene_wizard))


async def test_enter_via_callback_query(
    scene: GenreSelectorScene,
    mocked_bot: MockedBot,
    fake_tg_callback_query: CallbackQuery,
    fake_tg_message: Message,
    user: models.User,
    sa_async_session: AsyncSession,
) -> None:
    scene.construct_message_keyboard = lambda user, session: awaitable(
        InlineKeyboardMarkup(inline_keyboard=[])
    )

    await scene.enter_via_callback_query(
        callback_query=fake_tg_callback_query,
        user=user,
        session=sa_async_session,
    )

    compare(
        mocked_bot.calls,
        [
            EditMessageText(
                chat_id=fake_tg_message.chat.id,
                message_id=fake_tg_message.message_id,
                **fmt.Bold("Genres:").as_kwargs(),
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[]),
            ).as_(mocked_bot)
        ],
    )


async def test_handle_back_button_click(
    scene: GenreSelectorScene,
    fake_tg_callback_query: CallbackQuery,
    scene_wizard: FakeSceneWizard,
) -> None:
    await scene.handle_back_button_click(fake_tg_callback_query)

    assert scene_wizard.scene_actions == [BackSceneAction()]


async def test_construct_message_keyboard(
    scene: GenreSelectorScene,
    user: models.User,
    sa_async_session: AsyncSession,
) -> None:
    all_genres = [models.Genre(name=f"Genre #{i}") for i in range(1, 6)]
    sa_async_session.add_all(all_genres)

    await user.select_genre(all_genres[0])
    await user.select_genre(all_genres[3])

    await sa_async_session.flush()

    keyboard = await scene.construct_message_keyboard(user, sa_async_session)
    assert keyboard == InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"{constants.CHECKED_CHECKBOX} Genre #1",
                    callback_data=GenreButtonCD(genre_id=1, selected=False).pack(),
                ),
                InlineKeyboardButton(
                    text=f"{constants.UNCHECKED_CHECKBOX} Genre #2",
                    callback_data=GenreButtonCD(genre_id=2, selected=True).pack(),
                ),
                InlineKeyboardButton(
                    text=f"{constants.UNCHECKED_CHECKBOX} Genre #3",
                    callback_data=GenreButtonCD(genre_id=3, selected=True).pack(),
                ),
            ],
            [
                InlineKeyboardButton(
                    text=f"{constants.CHECKED_CHECKBOX} Genre #4",
                    callback_data=GenreButtonCD(genre_id=4, selected=False).pack(),
                ),
                InlineKeyboardButton(
                    text=f"{constants.UNCHECKED_CHECKBOX} Genre #5",
                    callback_data=GenreButtonCD(genre_id=5, selected=True).pack(),
                ),
            ],
            [
                InlineKeyboardButton(
                    text=constants.BACK_BUTTON_TEXT,
                    callback_data=constants.BACK_BUTTON_CD,
                )
            ],
        ]
    )


async def test_handle_genre_button_clicked_selected(
    scene: GenreSelectorScene,
    user: models.User,
    sa_async_session: AsyncSession,
    fake_tg_callback_query: CallbackQuery,
    fake_tg_message: Message,
    genre: models.Genre,
    mocked_bot: MockedBot,
    scene_wizard: FakeSceneWizard,
) -> None:
    callback_data = GenreButtonCD(
        genre_id=genre.id,
        selected=True,
    )

    await scene.handle_genre_button_click(
        callback_query=fake_tg_callback_query,
        user=user,
        callback_data=callback_data,
        session=sa_async_session,
    )

    await sa_async_session.refresh(user)
    assert await user.awaitable_attrs.selected_genres == {genre}
    assert scene_wizard.scene_actions == [
        RetakeSceneAction(data={"_with_history": False})
    ]


async def test_handle_genre_button_clicked_deselected(
    scene: GenreSelectorScene,
    user: models.User,
    sa_async_session: AsyncSession,
    fake_tg_callback_query: CallbackQuery,
    genre: models.Genre,
    scene_wizard: FakeSceneWizard,
) -> None:
    await user.select_genre(genre)
    callback_data = GenreButtonCD(
        genre_id=genre.id,
        selected=False,
    )

    await scene.handle_genre_button_click(
        callback_query=fake_tg_callback_query,
        user=user,
        callback_data=callback_data,
        session=sa_async_session,
    )

    await sa_async_session.refresh(user)
    assert not await user.awaitable_attrs.selected_title_types
    assert scene_wizard.scene_actions == [
        RetakeSceneAction(data={"_with_history": False})
    ]
