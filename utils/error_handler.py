"""
Модуль для обработки ошибок в Telegram-боте.

Этот модуль содержит функцию-обработчик ошибок, которая отлавливает исключение `TelegramBadRequest`,
возникающее, когда сообщение превышает максимальную длину, установленную Telegram.
Вместо аварийного завершения работы, бот информирует пользователя о невозможности
отправить слишком длинное сообщение.

Функции:
    handle_message_too_long(event, bot): Асинхронно обрабатывает ошибки слишком длинных сообщений.
"""
import logging
from aiogram.types import Update, ErrorEvent
from aiogram.exceptions import TelegramBadRequest

# Включаем логирование для отслеживания ошибок
logger = logging.getLogger(__name__)

async def handle_message_too_long(event: ErrorEvent, bot) -> None:
    """
    Обрабатывает исключение `TelegramBadRequest`, когда сообщение слишком длинное.

    Эта функция вызывается, когда возникает исключение `TelegramBadRequest`
    с сообщением, указывающим, что сообщение слишком длинное ("message is too long").
    Она извлекает ID чата из события и отправляет пользователю уведомление
    о том, что результат слишком велик для отображения.

    Args:
        event (ErrorEvent): Объект события, содержащий информацию об ошибке.
        bot: Экземпляр бота для отправки ответного сообщения.

    Returns:
        None
    """
    logger.error(f"Ошибка BadRequest: {event.exception}")
    # Проверяем, что ошибка связана с длиной сообщения
    if isinstance(event.exception, TelegramBadRequest) and "message is too long" in str(event.exception):
        # Получаем chat_id из объекта события
        chat_id = _get_chat_id_from_event(event)
        if chat_id:
            # Отправляем пользователю сообщение об ошибке
            await bot.send_message(
                chat_id=chat_id,
                text="Результат получился слишком большим и я не могу его отправить."
            )

def _get_chat_id_from_event(event: ErrorEvent) -> int | None:
    """
    Извлекает идентификатор чата из объекта события.

    Args:
        event (ErrorEvent): Объект события Telegram.

    Returns:
        int | None: Идентификатор чата, если он найден, иначе None.
    """
    if event.update and event.update.message:
        return event.update.message.chat.id
    if event.update and event.update.callback_query:
        return event.update.callback_query.message.chat.id
    return None
