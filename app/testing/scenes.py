from dataclasses import dataclass, field
from typing import Any

from aiogram.fsm.context import FSMContext
from aiogram.fsm.scene import Scene


@dataclass(kw_only=True)
class _SceneAction:
    data: dict[str, Any] = field(default_factory=dict)


@dataclass
class ExitSceneAction(_SceneAction):
    pass


@dataclass
class BackSceneAction(_SceneAction):
    pass


@dataclass
class GoToSceneAction(_SceneAction):
    scene: type[Scene] | str


class RetakeSceneAction(_SceneAction):
    pass


type SceneAction = (
    ExitSceneAction | BackSceneAction | GoToSceneAction | RetakeSceneAction
)


class FakeSceneWizard:
    """This a fake scene wizard that mimics ``aiogram.fsm.scene.SceneWizard``.

    Unlike the original one, it doesn't require a ``SceneManager``. All the scene
    navigation methods are stubs that only record that an action was called in
    ``self.scene_actions``.

    :ivar state: An instance of ``FSMContext`` that is used the same way as in
        the original ``SceneWizard`` (see ``SceneWizard.state``).
    :ivar scene_actions: A list of recorded scene navigation actions.
    """

    def __init__(self, state: FSMContext):
        self.state = state

        self.scene_actions: list[SceneAction] = []

    async def exit(self, **kwargs: Any) -> None:
        """Add an ``ExitSceneAction`` to ``self.scene_actions``.

        :param kwargs: All kwargs are passed as the ``data`` parameter
            to the ``ExitSceneAction``.
        :return: None
        """
        self.scene_actions.append(ExitSceneAction(data=kwargs))

    async def back(self, **kwargs: Any) -> None:
        """Add a ``BackSceneAction`` to ``self.scene_actions``.

        :param kwargs: All kwargs are passed as the ``data`` parameter
            to the ``BackSceneAction``.
        :return: None
        """
        self.scene_actions.append(BackSceneAction(data=kwargs))

    async def retake(self, **kwargs: Any) -> None:
        """Add a ``RetakeSceneAction`` to ``self.scene_actions``.

        :param kwargs: All kwargs are passed as the ``data`` parameter
            to the ``RetakeSceneAction``.
        :return: None
        """
        self.scene_actions.append(RetakeSceneAction(data=kwargs))

    async def goto(self, scene: type[Scene] | str, **kwargs: Any) -> None:
        """Add a ``GoToSceneAction`` to ``self.scene_actions``.

        :param scene: The scene to navigate to. Passed as the ``scene`` parameter to
            the ``GoToSceneAction``.
        :param kwargs: All kwargs are passed as the ``data`` parameter
            to the ``GoToSceneAction``.
        :return: None
        """
        self.scene_actions.append(GoToSceneAction(scene=scene, data=kwargs))

    async def set_data(self, data: dict[str, Any]) -> None:
        """
        Sets custom data in the current state.

        :param data: A dictionary containing the custom data to be set in the current
            state.
        :return: None
        """
        await self.state.set_data(data=data)

    async def get_data(self) -> dict[str, Any]:
        """
        This method returns the data stored in the current state.

        :return: A dictionary containing the data stored in the scene state.
        """
        return await self.state.get_data()

    async def get_value(self, key: str, default: Any = None) -> Any:
        return await self.state.get_value(key, default)

    async def update_data(
        self, data: dict[str, Any] | None = None, **kwargs: Any
    ) -> dict[str, Any]:
        """
        This method updates the data stored in the current state

        :param data: Optional dictionary of data to update.
        :param kwargs: Additional key-value pairs of data to update.
        :return: Dictionary of updated data
        """
        if data:
            kwargs.update(data)
        return await self.state.update_data(data=kwargs)

    async def clear_data(self) -> None:
        """
        Clears the data.

        :return: None
        """
        await self.set_data({})
