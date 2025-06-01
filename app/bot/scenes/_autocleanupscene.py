import itertools
import operator
from collections.abc import Iterable
from typing import NamedTuple

import aiogram.exceptions
import aiogram.types
from aiogram.fsm.scene import Scene, on
from loguru import logger


class MessageToDelete(NamedTuple):
    message_id: int
    chat_id: int


class AutoCleanupScene(Scene):
    @on.message.exit()
    async def exit_via_message(
        self, message: aiogram.types.Message, bot: aiogram.Bot
    ) -> None:
        """This method is called when the user exits the scene via a message.
        It should clean up the screen from any leftover messages."""

        logger.debug("Exiting via a message.")

        await self.cleanup(bot)

        logger.info("Exited")

    async def register_for_cleanup(self, message: aiogram.types.Message) -> None:
        """Register a message for cleanup.

        :param message: A message that should be cleaned up latter.
        """

        messages_to_delete: set[MessageToDelete] = await self._get_messages_to_delete()
        messages_to_delete.add(MessageToDelete(message.message_id, message.chat.id))
        await self._set_messages_to_delete(messages_to_delete)
        logger.debug(
            f"Message message_id={message.message_id} chat_id={message.chat.id} "
            "registered for cleanup"
        )

    async def cleanup(self, bot: aiogram.Bot) -> None:
        """Delete messages registered for cleanup

        :param bot: A bot instance that will be used to delete messages.
        """
        logger.debug("Cleaning up messages")

        messages_to_delete = await self._get_messages_to_delete()

        # Group messages by chat_id to delete them in bulk
        chat_id_getter = operator.itemgetter(1)
        messages_to_delete = sorted(messages_to_delete, key=chat_id_getter)
        for chat_id, messages in itertools.groupby(messages_to_delete, chat_id_getter):
            messages = [message_id for message_id, _ in messages]

            logger.debug(f"Deleting messages chat_id={chat_id} messages={messages}")
            try:
                await bot.delete_messages(chat_id=chat_id, message_ids=messages)
            except aiogram.exceptions.TelegramBadRequest as e:
                logger.warning(
                    f"Failed to clean up messages in chat id={chat_id}. Reason: {e}"
                )

    async def _get_messages_to_delete(self) -> set[MessageToDelete]:
        """Load and deserialize messages to delete from the FSM context."""

        messages_to_delete = await self.wizard.get_value("messages_to_delete", [])
        return {
            MessageToDelete(message_id, chat_id)
            for message_id, chat_id in messages_to_delete
        }

    async def _set_messages_to_delete(
        self, messages_to_delete: Iterable[MessageToDelete]
    ) -> None:
        """Serialize and save messages to delete to the FSM context."""
        await self.wizard.update_data(messages_to_delete=list(messages_to_delete))
