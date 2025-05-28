import aiogram
from aiogram.fsm.scene import SceneRegistry

from .settingsscene import SettingsScene


# Scenes should be registered to the dispatcher to have the scene middleware
# available across all routers.
def setup_dispatcher(dispatcher: aiogram.Dispatcher) -> None:
    """Register scenes to the dispatcher.

    :param dispatcher: The dispatcher to register scenes to.
    """

    scene_registry = SceneRegistry(dispatcher)
    scene_registry.register(SettingsScene)
