import aiogram as _aiogram
import aiogram.fsm.scene as _scenes

from .suggestionscene import SuggestionScene
from .titlefiltersscene import TitleFilterScene


def register_in_router(router: _aiogram.Router) -> None:
    _scenes.SceneRegistry(router).add(
        SuggestionScene,
        TitleFilterScene,
    )
