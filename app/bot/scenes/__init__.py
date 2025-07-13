import aiogram
from aiogram.fsm.scene import SceneRegistry

from .genreselectorscene import GenreSelectorScene
from .minimummovieratingselectorscene import MinimumMovieRatingSelectorScene
from .minimummovievotesselectorscene import MinimumMovieVotesSelectorScene
from .settingsscene import SettingsScene
from .suggestionscene import SuggestionScene
from .titletypeselectorscene import TitleTypeSelectorScene

ALL_SCENES = [
    GenreSelectorScene,
    SettingsScene,
    TitleTypeSelectorScene,
    MinimumMovieRatingSelectorScene,
    MinimumMovieVotesSelectorScene,
    SuggestionScene,
]


# Scenes should be registered to the dispatcher to have the scene middleware
# available across all routers.
def setup_dispatcher(dispatcher: aiogram.Dispatcher) -> None:
    """Register scenes to the dispatcher.

    :param dispatcher: The dispatcher to register scenes to.
    """

    scene_registry = SceneRegistry(dispatcher)
    scene_registry.register(*ALL_SCENES)
