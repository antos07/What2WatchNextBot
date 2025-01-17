import aiogram as _aiogram
import aiogram.fsm.scene as _scenes

from .filtersettingsscene import FilterSettingsScene
from .suggestionscene import SuggestionScene


def register_in_router(router: _aiogram.Router) -> None:
    _scenes.SceneRegistry(router).add(
        SuggestionScene,
        FilterSettingsScene,
    )
