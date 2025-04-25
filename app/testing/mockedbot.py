import pathlib
from typing import BinaryIO, Optional, Union
from unittest import mock

import aiogram
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.methods import TelegramMethod

from app.testing.constants import BOT_TOKEN


class MockedBot(aiogram.Bot):
    """A mocked bot that records all method calls.

    If an actual method result is needed, patch appropriate methods.
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(
            token=kwargs.pop("token", BOT_TOKEN),
            session=mock.MagicMock(spec=AiohttpSession),
        )

        self._me = aiogram.types.User(
            id=self.id,
            is_bot=True,
            first_name="Test",
            last_name="Bot",
            username="testbot",
            language_code="en",
        )

        self.calls = []

    async def __call__[T](
        self, method: TelegramMethod[T], request_timeout: Optional[int] = None
    ) -> T:
        self.calls.append(method)
        return mock.Mock()

    async def download_file(
        self,
        file_path: Union[str, pathlib.Path],
        destination: Optional[Union[BinaryIO, pathlib.Path, str]] = None,
        timeout: int = 30,
        chunk_size: int = 65536,
        seek: bool = True,
    ) -> Optional[BinaryIO]:
        raise RuntimeError(
            "No file downloads in a mocked bot. Patch this method if needed."
        )
