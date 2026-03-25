from aiogram.utils.keyboard import InlineKeyboardBuilder

# Главное меню
def get_main_kb():
    builder = InlineKeyboardBuilder()

    builder.button(text="Функции", callback_data="menu_utils", icon_custom_emoji_id="5226512880362332956", style="primary")
    builder.adjust(1) # Скорректировано под одну кнопку
    return builder.as_markup()

# Меню Функций
def get_utils_kb():
    builder = InlineKeyboardBuilder()

    builder.button(text="Назад", callback_data="main_menu", icon_custom_emoji_id="5328091751720694986", style="danger")
    builder.adjust(1)
    return builder.as_markup()