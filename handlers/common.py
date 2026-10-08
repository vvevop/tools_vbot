from aiogram import Router, F, types
from aiogram.filters import Command
from keyboards.builders import get_main_kb

router = Router()

# Обработчик команды /start
@router.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.reply("<tg-emoji emoji-id='5341715473882955310'>⚙️</tg-emoji> <b>Главное меню:</b>", reply_markup=get_main_kb())

# Обработчик кнопки "Назад" в меню функций
@router.callback_query(F.data == "main_menu")
async def handle_main_menu(callback: types.CallbackQuery):
    await callback.message.edit_text("<tg-emoji emoji-id='5341715473882955310'>⚙️</tg-emoji> <b>Главное меню:</b>", reply_markup=get_main_kb())