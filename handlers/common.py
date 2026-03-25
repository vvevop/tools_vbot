from aiogram import Router, F, types
from aiogram.filters import Command
from keyboards.builders import get_main_kb

router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    # await message.delete()

    await message.answer("<tg-emoji emoji-id='5341715473882955310'>⚙️</tg-emoji> <b>Главное меню:</b>", reply_markup=get_main_kb())

@router.callback_query(F.data == "main_menu")
async def handle_main_menu(callback: types.CallbackQuery):
    await callback.message.edit_text("🏠 Главное меню:", reply_markup=get_main_kb())

@router.callback_query(F.data == "delete_msg")
async def handle_delete_msg(callback: types.CallbackQuery):
    await callback.message.delete()
