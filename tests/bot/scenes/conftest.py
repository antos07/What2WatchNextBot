import pytest
from aiogram.fsm.context import FSMContext

from app.testing.scenes import FakeSceneWizard


@pytest.fixture()
def scene_wizard(fsm_context: FSMContext) -> FakeSceneWizard:
    return FakeSceneWizard(fsm_context)
