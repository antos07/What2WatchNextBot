from typing import cast
from unittest import mock

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
from app.bot.scenes import TitleTypeSelectorScene
from app.bot.scenes.titletypeselectorscene import TitleTypeButton
from app.core import models
from app.testing.mockedbot import MockedBot
from app.testing.scenes import BackSceneAction, FakeSceneWizard, RetakeSceneAction
from app.utils import awaitable


@pytest.fixture()
def scene(scene_wizard: FakeSceneWizard) -> TitleTypeSelectorScene:
    return TitleTypeSelectorScene(cast(SceneWizard, scene_wizard))


async def test_enter_via_callback_query(
    scene: TitleTypeSelectorScene,
    mocked_bot: MockedBot,
    fake_tg_callback_query: CallbackQuery,
    fake_tg_message: Message,
) -> None:
    async def fake_construct_message_keyboard(user, session):
        return InlineKeyboardMarkup(inline_keyboard=[])

    scene.construct_message_keyboard = mock.AsyncMock(
        side_effect=fake_construct_message_keyboard
    )

    await scene.enter_via_callback_query(
        callback_query=fake_tg_callback_query,
        user=mock.Mock(),
        session=mock.Mock(),
    )

    compare(
        actual=mocked_bot.calls,
        expected=[
            EditMessageText(
                **fmt.Bold("Title Types:").as_kwargs(),
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[]),
                message_id=fake_tg_message.message_id,
                chat_id=fake_tg_message.chat.id,
            )
        ],
    )
    scene.construct_message_keyboard.assert_called_once()


async def test_exit_via_message(
    scene: TitleTypeSelectorScene, mocked_bot: MockedBot, fake_tg_message: Message
) -> None:
    scene.cleanup = mock.AsyncMock()

    await scene.exit_via_message(fake_tg_message, mocked_bot)

    scene.cleanup.assert_called_once_with(mocked_bot)


async def test_handle_back_button_click(
    scene: TitleTypeSelectorScene,
    scene_wizard: FakeSceneWizard,
    fake_tg_callback_query: CallbackQuery,
) -> None:
    await scene.handle_back_button_click(fake_tg_callback_query)

    assert scene_wizard.scene_actions == [BackSceneAction()]


async def test_construct_message_keyboard(
    scene: TitleTypeSelectorScene,
    user: models.User,
    sa_async_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    all_title_types = [models.TitleType(name="t1"), models.TitleType(name="t2")]
    all_title_types[0].id = 1
    all_title_types[1].id = 2

    monkeypatch.setattr(
        "app.core.services.title_type.list_all",
        lambda session: awaitable(all_title_types),
    )

    await user.awaitable_attrs.selected_title_types
    user.selected_title_types = {all_title_types[0]}

    keyboard = await scene.construct_message_keyboard(user, sa_async_session)

    assert keyboard == InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"{constants.CHECKED_CHECKBOX} T1",
                    callback_data=TitleTypeButton(
                        title_type_id=1, selected=False
                    ).pack(),
                ),
                InlineKeyboardButton(
                    text=f"{constants.UNCHECKED_CHECKBOX} T2",
                    callback_data=TitleTypeButton(
                        title_type_id=2, selected=True
                    ).pack(),
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


async def test_handle_title_type_button_clicked_selected(
    scene: TitleTypeSelectorScene,
    user: models.User,
    sa_async_session: AsyncSession,
    fake_tg_callback_query: CallbackQuery,
    fake_tg_message: Message,
    title_type: models.TitleType,
    mocked_bot: MockedBot,
    scene_wizard: FakeSceneWizard,
) -> None:
    callback_data = TitleTypeButton(
        title_type_id=title_type.id,
        selected=True,
    )

    await scene.handle_title_type_button_click(
        callback_query=fake_tg_callback_query,
        user=user,
        callback_data=callback_data,
        session=sa_async_session,
    )

    await sa_async_session.refresh(user)
    assert await user.awaitable_attrs.selected_title_types == {title_type}
    assert scene_wizard.scene_actions == [
        RetakeSceneAction(data={"_with_history": False})
    ]


async def test_handle_title_type_button_clicked_deselected(
    scene: TitleTypeSelectorScene,
    user: models.User,
    sa_async_session: AsyncSession,
    fake_tg_callback_query: CallbackQuery,
    title_type: models.TitleType,
    scene_wizard: FakeSceneWizard,
) -> None:
    await user.select_title_type(title_type)
    callback_data = TitleTypeButton(
        title_type_id=title_type.id,
        selected=False,
    )

    await scene.handle_title_type_button_click(
        callback_query=fake_tg_callback_query,
        user=user,
        callback_data=callback_data,
        session=sa_async_session,
    )

    assert not user.selected_title_types

    await sa_async_session.refresh(user)
    assert not await user.awaitable_attrs.selected_title_types
    assert scene_wizard.scene_actions == [
        RetakeSceneAction(data={"_with_history": False})
    ]
