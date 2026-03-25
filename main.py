import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.types import (
    BotCommand,
    BotCommandScopeDefault,
    BotCommandScopeAllPrivateChats,
    BotCommandScopeAllGroupChats,
    BotCommandScopeChat,
    BotCommandScopeChatAdministrators
)
from aiogram.client.default import DefaultBotProperties

from config import BOT_TOKEN
from handlers import common, tools # Removed admin, server

# Настройка логгирования
logging.basicConfig(level=logging.INFO)

# Установка команд бота
async def set_commands(bot: Bot):
    main_commands = [
        BotCommand(command="start", description="Главное меню"),
        BotCommand(command="qr", description="Текст → QR-код"),
        BotCommand(command="enc64", description="Text → Base64"),
        BotCommand(command="dec64", description="Base64 → Text"),
    ]
    
    await bot.set_my_commands(
        commands=main_commands, 
        scope=BotCommandScopeAllPrivateChats()
    )

    await bot.set_my_commands(
        commands=main_commands, 
        scope=BotCommandScopeAllGroupChats()
    )

async def main():
    # Инициализация бота
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode='HTML')
    )

    dp = Dispatcher()

    dp.startup.register(set_commands)

    # РЕГИСТРАЦИЯ РОУТЕРОВ
    dp.include_router(common.router)
    dp.include_router(tools.router)

    # Удаляем вебхуки (на всякий случай) и запускаем
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот выключен")
