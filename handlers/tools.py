import io
import html
import qrcode
from aiogram import Router, F, Bot, types
from aiogram.types import Message, LinkPreviewOptions, BufferedInputFile
from aiogram.filters import Command, CommandObject
from aiogram.enums import ChatAction

from utils.web import upload_to_x0
from keyboards.builders import get_utils_kb

router = Router()

# --- Шпаргалка ---
@router.callback_query(F.data == "menu_utils")
async def handle_utils_menu(callback: types.CallbackQuery):
    await callback.message.edit_text(
        """🛠 <b>Доступные функции:</b>

Эти инструменты работают <b>всегда</b>:

<tg-emoji emoji-id='5775949822993371030'>🖼</tg-emoji> <b>Фото</b> — прямая ссылка (x0.at)
<tg-emoji emoji-id='5784982040432611567'>🙂</tg-emoji> <b>Стикер</b> — получение File ID
<tg-emoji emoji-id='5956148757899776734'>⭐️</tg-emoji> Текст, содержащий <b>Premium эмодзи</b> — коды для вставки всех кастомных эмодзи из текста

<b>Команды:</b>
<code>/qr [текст]</code> — генерация QR-кода

""",
        reply_markup=get_utils_kb()
    )

# Обработка фотографий 
async def process_photo_message(message: Message):
    await message.bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.UPLOAD_PHOTO)
    try:
        photo = message.photo[-1]
        file_io = io.BytesIO()
        await message.bot.download(file=photo, destination=file_io)
        file_io.seek(0)

        url = await upload_to_x0(file_io, "image.jpg", "image/jpeg")
        if url:
            await message.reply(
                f'<a href="{url}">⁡</a>',
                link_preview_options=LinkPreviewOptions(is_disabled=True)
            )
        else:
            await message.answer("❌ Ошибка загрузки на сервис.")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")

# Обработка стикеров 
async def process_sticker_message(message: Message):
    await message.bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)
    await message.reply(f"<code>{message.sticker.file_id}</code>")

# --- Загрузка фото ---
@router.message(F.photo, F.chat.type == "private")
async def auto_photo_handler_private(message: Message):
    await process_photo_message(message)

# --- ID стикера ---
@router.message(F.sticker, F.chat.type == "private")
async def get_sticker_id_private(message: Message):
    await process_sticker_message(message)

# Новый обработчик для ответов в группах, где упоминается бот
@router.message(F.reply_to_message, F.chat.type.in_({"group", "supergroup"}))
async def handle_group_reply_media(message: Message):
    me = await message.bot.get_me()
    bot_username = me.username
    text_content = message.text or message.caption or ""

    if f"@{bot_username}" in text_content:
        reply = message.reply_to_message
        if reply.photo:
            await process_photo_message(reply)
        elif reply.sticker:
            await process_sticker_message(reply)

# --- Код эмодзи из текста ---
@router.message(F.chat.type == "private", F.entities.len() > 0, ~F.text.startswith("/"))
async def get_emoji_id(message: Message):
    await message.bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)

    # Ищем кастомные эмодзи во всем сообщении
    custom_emojis = [e for e in (message.entities or []) if e.type == "custom_emoji"]
    
    if not custom_emojis:
        return # Если нет кастомных эмодзи, игнорируем сообщение

    emoji_details = []
    total_emojis = len(custom_emojis) # Вычисляем общее количество эмодзи

    for emoji in custom_emojis:
        emoji_char = emoji.extract_from(message.text)
        emoji_id = emoji.custom_emoji_id
        
        # Формируем визуальный пример и код для копирования
        visual_emoji = f"<tg-emoji emoji-id='{emoji_id}'>{emoji_char}</tg-emoji>"
        code_for_copy = html.escape(visual_emoji)
        
        emoji_details.append(f"\n{visual_emoji}\n<code>{code_for_copy}</code>")

    # Объединяем все детали эмодзи в один блок цитаты
    all_emojis_block = ""
    if emoji_details: # Только если есть эмодзи, создаем блок
        all_emojis_block = f"<blockquote expandable>" + "\n".join(emoji_details) + "</blockquote>"
    
    # Отдельный блок для общего количества
    total_count_block = f"<blockquote>Всего: <b>{total_emojis}</b></blockquote>"

    response_parts = [part for part in [all_emojis_block, total_count_block] if part]
    await message.reply("\n\n".join(response_parts))

# --- Text → QR ---
@router.message(Command("qr"))
async def cmd_qr(message: types.Message, command: CommandObject):
    if not command.args:
        return await message.reply(
            "⚠️ Вы не ввели текст!\nИспользование: <code>/qr ваш_текст</code>"
        )

    await message.bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.UPLOAD_PHOTO)

    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(command.args)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

        await message.answer_photo(
            photo=BufferedInputFile(buffer.read(), filename="qr_code.png"),
            caption=f"✅ QR-код для текста:\n<blockquote>{command.args}</blockquote>"
        )
        
    except Exception as e:
        await message.answer(f"❌ Ошибка при генерации: {str(e)}")