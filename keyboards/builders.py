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

# Клавиатура для сокращенного варианта эмодзи
def get_short_emoji_options_kb(yes_callback_data: str):
    builder = InlineKeyboardBuilder()
    builder.button(text="Да", callback_data=yes_callback_data, icon_custom_emoji_id="6023940002008799618", style="success")
    builder.adjust(1)
    return builder.as_markup()

# Вобор действия с фото
def get_photo_action_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="Ссылка", callback_data="link_photo", icon_custom_emoji_id="5877465816030515018")
    builder.button(text="GIF", callback_data="gif_photo", icon_custom_emoji_id="5945068566909815651")
    builder.adjust(2)
    return builder.as_markup()