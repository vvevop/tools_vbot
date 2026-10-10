import io
import html
import qrcode
import base64
from typing import Tuple
import asyncio
import shutil
from pathlib import Path

from aiogram import Router, F, Bot, types
from aiogram.types import Message, LinkPreviewOptions, BufferedInputFile, FSInputFile, InputMediaAnimation, CallbackQuery
from aiogram.filters import Command, CommandObject
from aiogram.enums import ChatAction
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters.callback_data import CallbackData

from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# Создаем группу состояний
class PhotoVideoProcessing(StatesGroup):
    waiting_for_action = State()  # ждем действия с фото (ссылка или GIF)
    waiting_for_trim_choice = State()   # ждем выбора обрезки (да/нет) для видео

from utils.web import upload_to_x0
from keyboards.builders import get_utils_kb, get_short_emoji_options_kb, get_photo_action_kb

router = Router()

class EmojiIdCallback(CallbackData, prefix="emoji_id"):
    action: str # например, "send_short"
    original_message_id: int # ID сообщения, инициировавшего команду

# Вспомогательная функция для формирования текста ответа с эмодзи
def _generate_emoji_response_text(message: Message, include_code_for_copy: bool) -> Tuple[str, str]:
    custom_emojis = [e for e in (message.entities or []) if e.type == "custom_emoji"]

    if not custom_emojis:
        # Возвращать пустые строки для обеих частей, если не найдено пользовательских эмодзи.
        return "", ""

    emoji_details = []
    total_emojis = len(custom_emojis)

    for emoji in custom_emojis:
        emoji_char = emoji.extract_from(message.text)
        emoji_id = emoji.custom_emoji_id
        
        visual_emoji = f"<tg-emoji emoji-id='{emoji_id}'>{emoji_char}</tg-emoji>"
        detail_line = f"\n{visual_emoji}\n<code>{emoji_id}</code>"
        if include_code_for_copy:
            code_for_copy = html.escape(visual_emoji)
            detail_line += f"\n<code>{code_for_copy}</code>"
        emoji_details.append(detail_line)

    all_emojis_block = ""
    if emoji_details:
        all_emojis_block = f"<blockquote expandable>" + "\n".join(emoji_details) + "</blockquote>"
    
    total_count_block = f"<blockquote>Всего: <b>{total_emojis}</b></blockquote>"

    response_parts = [part for part in [all_emojis_block, total_count_block] if part]
    # Верните обе части в виде кортежа
    return "\n\n".join(response_parts), total_count_block

# --- Меню "Доступные функции" ---
@router.callback_query(F.data == "menu_utils")
async def handle_utils_menu(callback: CallbackQuery):
    await callback.message.edit_text(
"""<tg-emoji emoji-id='6021401276904905698'>🛠</tg-emoji> <b>Доступные функции:</b>

Эти инструменты работают <b>всегда</b>:

<tg-emoji emoji-id='5775949822993371030'>🖼</tg-emoji> <b>Фото</b> — прямая ссылка (x0.at)
<tg-emoji emoji-id='5784982040432611567'>🙂</tg-emoji> <b>Стикер</b> — получение File ID
<tg-emoji emoji-id='5956148757899776734'>⭐️</tg-emoji> Текст, содержащий <b>Premium эмодзи</b> — коды для вставки всех кастомных эмодзи из текста

<b>Команды:</b>
<code>/qr [текст]</code> — генерация QR-кода
<code>/enc64 [текст]</code> — кодирование текста в Base64
<code>/dec64 [base64_текст]</code> — декодирование текста из Base64
""",
        reply_markup=get_utils_kb()
    )

# Фото → Ссылка (x0.at)
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
            await message.answer("<tg-emoji emoji-id='5778527486270770928'>❌</tg-emoji> Ошибка загрузки на сервис.")
    except Exception as e:
        await message.answer(f"<tg-emoji emoji-id='5778527486270770928'>❌</tg-emoji> Ошибка: {str(e)}")

# Обработчик стикеров
async def process_sticker_message(message: Message):
    await message.bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)
    await message.reply(f"<code>{message.sticker.file_id}</code>")

# Обработчик фото
@router.message(F.photo, F.chat.type == "private")
async def photo_handler_private(message: Message, state: FSMContext):
    # Сохраняем file_id фото в данные состояния пользователя
    await state.update_data(current_photo_id=message.photo[-1].file_id)

    # Переводим пользователя в состояние ожидания действия
    await state.set_state(PhotoVideoProcessing.waiting_for_action)

    await message.reply(
        "<tg-emoji emoji-id='5807800879553715710'>❓</tg-emoji> Что сделать с фото?",
        reply_markup=get_photo_action_kb()
    )

# Фото → Ссылка (x0.at)
@router.callback_query(F.data == "link_photo")
async def handle_link_photo(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    photo_id = data.get("current_photo_id")

    await callback.message.bot.send_chat_action(chat_id=callback.message.chat.id, action=ChatAction.UPLOAD_PHOTO)
    try:
        file_io = io.BytesIO()
        await callback.message.bot.download(file=photo_id, destination=file_io)
        file_io.seek(0)

        url = await upload_to_x0(file_io, "image.jpg", "image/jpeg")
        if url:
            await callback.message.edit_text(
                f'<a href="{url}">⁡</a>',
                link_preview_options=LinkPreviewOptions(is_disabled=True)
            )
        else:
            await callback.message.edit_text("<tg-emoji emoji-id='5778527486270770928'>❌</tg-emoji> Ошибка загрузки на сервис.")
    except Exception as e:
        await callback.message.edit_text(f"<tg-emoji emoji-id='5778527486270770928'>❌</tg-emoji> Ошибка: {str(e)}")
    finally:
        await state.clear()

# Фото → GIF (5-секундное видео)
@router.callback_query(F.data == "gif_photo", PhotoVideoProcessing.waiting_for_action)
async def handle_gif_photo(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    photo_id = data.get("current_photo_id")

    if not photo_id:
        await callback.message.edit_text("<tg-emoji emoji-id='5778527486270770928'>❌</tg-emoji> Фото не найдено")
        await state.clear()
        return

    ffmpeg = shutil.which("ffmpeg") or shutil.which("ffmpeg.exe")
    if not ffmpeg:
        await callback.message.edit_text("<tg-emoji emoji-id='5778527486270770928'>❌</tg-emoji> ffmpeg не найден")
        await state.clear()
        return

    await callback.answer("⏳ Обрабатываю...")
    await callback.message.bot.send_chat_action(
        chat_id=callback.message.chat.id,
        action=ChatAction.UPLOAD_VIDEO
    )

    input_path = Path("temp_photo.jpg")
    output_path = Path("gif.mp4")

    try:
        # Скачиваем фото
        file = await callback.message.bot.get_file(photo_id)
        await callback.message.bot.download_file(file.file_path, destination=input_path)

        # Фото → 5-секундное бесшумное видео
        process = await asyncio.create_subprocess_exec(
            ffmpeg, "-y",
            "-loop", "1",
            "-i", str(input_path),
            "-c:v", "libx264",
            "-t", "5",
            "-pix_fmt", "yuv420p",
            "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2",
            "-an",
            str(output_path),
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.PIPE
        )
        _, stderr = await process.communicate()

        if process.returncode != 0:
            raise Exception(stderr.decode(errors="ignore")[-400:])

        # === Главное отличие ===
        # Отправляем как Animation (GIF), а не как Video
        animation = FSInputFile(output_path)
        await callback.message.edit_media(
            media=InputMediaAnimation(media=animation, caption="")
        )

    except Exception as e:
        await callback.message.edit_text(f"<tg-emoji emoji-id='5778527486270770928'>❌</tg-emoji> Ошибка:\n<code>{e}</code>")
    finally:
        for f in (input_path, output_path):
            if f.exists():
                try:
                    f.unlink()
                except Exception:
                    pass
        await state.clear()

# ID стикера
@router.message(F.sticker, F.chat.type == "private")
async def get_sticker_id_private(message: Message):
    await process_sticker_message(message)

# Обработчик для ответов в группах, где упоминается бот
@router.message(F.reply_to_message, F.chat.type.in_({"group", "supergroup"}))
async def handle_group_reply_media(message: Message, state: FSMContext):
    me = await message.bot.get_me()
    bot_username = me.username
    text_content = message.text or message.caption or ""

    # Проверяем, упомянут ли бот в сообщении, которое является ответом
    if f"@{bot_username}" in text_content:
        replied_message = message.reply_to_message # Сообщение, на которое ответили (содержит медиа/эмодзи)
        if replied_message.photo:
            # Сохраняем file_id фото в данные состояния пользователя
            await state.update_data(current_photo_id=replied_message.photo[-1].file_id)
            
            # Переводим пользователя в состояние ожидания действия
            await state.set_state(PhotoVideoProcessing.waiting_for_action)
            
            await replied_message.reply(
                "<tg-emoji emoji-id='5807800879553715710'>❓</tg-emoji> Что сделать с фото?",
                reply_markup=get_photo_action_kb()
            )
        elif replied_message.sticker:
            # Обрабатываем стикер из ответного сообщения
            await process_sticker_message(replied_message)
        elif [e for e in (replied_message.entities or []) if e.type == "custom_emoji"]:
            # Если отвеченное сообщение содержит пользовательские эмодзи
            await message.bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)
            full_response_text, total_count_block = _generate_emoji_response_text(replied_message, include_code_for_copy=True)
            if not full_response_text:
                await replied_message.reply("Не удалось найти премиум эмодзи в ответном сообщении.")
                return

            try:
                # Отвечаем на сообщение с эмодзи
                await replied_message.reply(full_response_text)
            except TelegramBadRequest as e:
                if "message is too long" in str(e):
                    # Создаем инлайн-клавиатуру для сокращенной версии
                    yes_callback_data = EmojiIdCallback(action="send_short_yes", original_message_id=replied_message.message_id).pack()
                    keyboard = get_short_emoji_options_kb(yes_callback_data)
                    await replied_message.reply(
                        "<tg-emoji emoji-id='5778527486270770928'>❌</tg-emoji> Результат получился слишком большим.\n"
                        "<tg-emoji emoji-id='5807800879553715710'>❓</tg-emoji> <b>Отправить сокращенный вариант?</b>\n\n"
                        f"{total_count_block}",
                        reply_markup=keyboard
                    )
                else:
                    await replied_message.reply(f"<tg-emoji emoji-id='5778527486270770928'>❌</tg-emoji> Произошла ошибка Telegram: {str(e)}")
            except Exception as e:
                await replied_message.reply(f"<tg-emoji emoji-id='5778527486270770928'>❌</tg-emoji> Произошла непредвиденная ошибка: {str(e)}")

# Код эмодзи из текста
@router.message(F.chat.type == "private", F.entities.len() > 0, ~F.text.startswith("/"))
async def get_emoji_id(message: Message):
    await message.bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)

    full_response_text, total_count_block = _generate_emoji_response_text(message, include_code_for_copy=True)
    if not full_response_text:
        return # Кастомные эмодзи не найдены

    try:
        await message.reply(full_response_text)
    except TelegramBadRequest as e:
        if "message is too long" in str(e):
            # Создаем inline клавиатуру для краткой версии
            yes_callback_data = EmojiIdCallback(action="send_short_yes", original_message_id=message.message_id).pack()
            keyboard = get_short_emoji_options_kb(yes_callback_data)
            await message.reply(
                "<tg-emoji emoji-id='5778527486270770928'>❌</tg-emoji> Результат получился слишком большим.\n"
                "<tg-emoji emoji-id='5807800879553715710'>❓</tg-emoji> <b>Отправить сокращенный вариант?</b>\n\n"
                f"{total_count_block}",
                reply_markup=keyboard
            )
        else:
            await message.answer(f"<tg-emoji emoji-id='5778527486270770928'>❌</tg-emoji> Произошла ошибка Telegram: {str(e)}")
    except Exception as e:
        await message.answer(f"<tg-emoji emoji-id='5778527486270770928'>❌</tg-emoji> Произошла непредвиденная ошибка: {str(e)}")

# Обработчик для кнопки «Да», отправляющий короткий ID эмодзи и удаляющий исходное сообщение
@router.callback_query(EmojiIdCallback.filter(F.action == "send_short_yes"))
async def handle_send_short_yes(callback: CallbackQuery, callback_data: EmojiIdCallback):
    """
    Обрабатывает нажатие кнопки "Да" для отправки сокращенной версии ID эмодзи.
    После отправки удаляет сообщение бота с кнопками.
    """
    await callback.answer("Подготавливаю сокращенный вариант...")

    original_user_message = callback.message.reply_to_message

    if not original_user_message:
        await callback.message.edit_text("Не удалось найти исходное сообщение для сокращенной версии.")
        return

    short_response_text, _ = _generate_emoji_response_text(original_user_message, include_code_for_copy=False)

    if not short_response_text:
        await callback.message.edit_text("Сокращенный вариант пуст.")
        return

    try:
        # Редактируем предыдущее сообщение бота (то, что с кнопкой), чтобы отобразить короткий текст.
        await callback.message.edit_text(short_response_text, reply_markup=None)
    except TelegramBadRequest as e:
        await callback.message.edit_text(f"<tg-emoji emoji-id='5778527486270770928'>❌</tg-emoji> Не удалось отправить сокращенный вариант: {str(e)}")
    except Exception as e:
        await callback.message.edit_text(f"<tg-emoji emoji-id='5778527486270770928'>❌</tg-emoji> Произошла непредвиденная ошибка при отправке сокращенной версии: {str(e)}")

# Text → QR
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
        await message.answer(f"<tg-emoji emoji-id='5778527486270770928'>❌</tg-emoji> Ошибка при генерации: {str(e)}")

# Text → Base64
@router.message(Command("enc64"))
async def cmd_enc64(message: types.Message, command: CommandObject):
    # Добавляем комментарий к функции: Кодирует введенный текст в формат Base64.
    if not command.args:
        return await message.reply(
            "⚠️ Вы не ввели текст для кодирования!\nИспользование: <code>/enc64 ваш_текст</code>"
        )
    
    await message.bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)

    try:
        encoded_bytes = base64.b64encode(command.args.encode('utf-8'))
        encoded_text = encoded_bytes.decode('utf-8')
        await message.reply(
            f"<code>{encoded_text}</code>"
        )
    except Exception as e:
        await message.answer(f"<tg-emoji emoji-id='5778527486270770928'>❌</tg-emoji> Ошибка при кодировании: {str(e)}")

# Base64 → Text
@router.message(Command("dec64"))
async def cmd_dec64(message: types.Message, command: CommandObject):
    # Добавляем комментарий к функции: Декодирует введенный текст из формата Base64.
    if not command.args:
        return await message.reply(
            "⚠️ Вы не ввели Base64 текст для декодирования!\nИспользование: <code>/dec64 ваш_base64_текст</code>"
        )
    
    await message.bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)

    try:
        decoded_bytes = base64.b64decode(command.args.encode('utf-8'))
        decoded_text = decoded_bytes.decode('utf-8')
        await message.reply(
            f"<code>{decoded_text}</code>"
        )
    except Exception as e:
        await message.answer(f"<tg-emoji emoji-id='5778527486270770928'>❌</tg-emoji> Ошибка при декодировании. Возможно, это не валидный Base64: {str(e)}")