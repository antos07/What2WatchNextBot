from typing import cast
from unittest import mock

import pytest
from aiogram.fsm.scene import SceneWizard
from aiogram.methods import DeleteMessages
from aiogram.types import Chat, Message, User
from testfixtures import SequenceComparison as S

from app.bot.scenes._autocleanupscene import AutoCleanupScene
from app.testing.constants import RANDOM_DATETIME
from app.testing.mockedbot import MockedBot
from app.testing.scenes import FakeSceneWizard

FAKE_MESSAGE = Message(
    message_id=1,
    date=RANDOM_DATETIME,
    chat=Chat(id=2, type="private", title="Test"),
    from_user=User(id=2, first_name="Test", is_bot=False),
    text="message",
)


@pytest.fixture()
def scene(scene_wizard: FakeSceneWizard) -> AutoCleanupScene:
    return AutoCleanupScene(cast(SceneWizard, scene_wizard))


async def test_exit_via_message(scene: AutoCleanupScene, mocked_bot: MockedBot) -> None:
    scene.cleanup = mock.AsyncMock()

    await scene.exit_via_message(FAKE_MESSAGE, mocked_bot)

    scene.cleanup.assert_called_once_with(mocked_bot)


async def test_register_for_cleanup_without_previous_messages(
    scene: AutoCleanupScene, mocked_bot: MockedBot, scene_wizard: FakeSceneWizard
) -> None:
    await scene.register_for_cleanup(FAKE_MESSAGE)

    assert await scene_wizard.get_value("messages_to_delete") == [
        (FAKE_MESSAGE.message_id, FAKE_MESSAGE.chat.id)
    ]


async def test_register_for_cleanup_with_previous_messages(
    scene: AutoCleanupScene, mocked_bot: MockedBot, scene_wizard: FakeSceneWizard
) -> None:
    await scene_wizard.update_data(messages_to_delete=[(0, 0)])

    await scene.register_for_cleanup(FAKE_MESSAGE)

    assert sorted(await scene_wizard.get_value("messages_to_delete")) == [
        (0, 0),
        (FAKE_MESSAGE.message_id, FAKE_MESSAGE.chat.id),
    ]


async def test_cleanup(
    scene: AutoCleanupScene, mocked_bot: MockedBot, scene_wizard: FakeSceneWizard
) -> None:
    await scene_wizard.update_data(messages_to_delete=[(0, 0), (1, 2), (2, 2), (3, 2)])

    await scene.cleanup(mocked_bot)

    assert mocked_bot.calls == [
        DeleteMessages(chat_id=0, message_ids=[0]),
        # Disable pydantic's validation
        DeleteMessages.model_construct(
            chat_id=2, message_ids=S(1, 2, 3, ordered=False)
        ),
    ]
    assert await scene_wizard.get_value("messages_to_delete") == []
