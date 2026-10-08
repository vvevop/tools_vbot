"""Обработка ошибки отправки слишком длинного сообщения в Telegram."""

import logging
from aiogram import Bot
from aiogram.types import ErrorEvent
from aiogram.exceptions import TelegramBadRequest

logger = logging.getLogger(__name__)


async def handle_message_too_long(event: ErrorEvent, bot: Bot) -> None:
    """Уведомляет пользователя, если ответ бота превысил лимит длины сообщения."""
    logger.error(f"Ошибка BadRequest: {event.exception}")

    if isinstance(event.exception, TelegramBadRequest) and "message is too long" in str(event.exception):
        if chat_id := _get_chat_id_from_event(event):
            await bot.send_message(
                chat_id=chat_id,
                text="Результат получился слишком большим и я не могу его отправить."
            )


def _get_chat_id_from_event(event: ErrorEvent) -> int | None:
    """Извлекает ID чата из входящего сообщения или callback-запроса."""
    if event.update and event.update.message:
        return event.update.message.chat.id
    if event.update and event.update.callback_query:
        return event.update.callback_query.message.chat.id
    return None