from aiogram.utils.keyboard import InlineKeyboardBuilder

# Главное меню
def get_main_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="📖 Функции", callback_data="menu_utils")
    builder.adjust(1) # Скорректировано под одну кнопку
    return builder.as_markup()

# Меню Функций
def get_utils_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ Назад", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()
