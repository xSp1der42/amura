import asyncio
import os
from threading import Thread
from dotenv import load_dotenv
from flask import Flask

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import CommandStart

# Загружаем данные
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
CHANNEL_ID = os.getenv("CHANNEL_ID")
CHAT_LINK = os.getenv("CHAT_LINK")
BOT_LINK = os.getenv("BOT_LINK")

# Формируем подпись
SIGNATURE = f"\n\n<a href='{CHAT_LINK}'>✅ Наш чат</a>\n<a href='{BOT_LINK}'>✅ Предложить новость</a>"

# Инициализируем бота
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# Функция генерации кнопок (зашиваем ID автора и ID сообщения прямо в кнопку)
def get_admin_keyboard(user_id: int, message_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Опубликовать", callback_data=f"appr:{user_id}:{message_id}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"rejl:{user_id}:{message_id}")
        ]
    ])


# 0. ОБРАБОТКА КОМАНДЫ /start
@dp.message(CommandStart())
async def cmd_start(message: Message):
    welcome_text = (
        "👋 Привет!\n\n"
        "Это бот предложки для: <b>Ищу тебя Казань</b>\n"
        "Отправь свое сообщение (фото с текстом или просто текст), и мы опубликуем его в наш канал"
    )
    await message.answer(welcome_text)


# 1. ЛОВИМ ФОТО С ТЕКСТОМ
@dp.message(F.photo)
async def handle_photo_post(message: Message):
    await message.reply("✅ Ваша новость отправлена на модерацию!")
    caption = message.html_text if message.html_text else ""
    
    # Отправляем админу с персональными кнопками
    await bot.send_photo(
        chat_id=ADMIN_ID,
        photo=message.photo[-1].file_id,
        caption=f"<b>Новая предложка:</b>\n\n{caption}",
        reply_markup=get_admin_keyboard(message.from_user.id, message.message_id)
    )


# 1.1 ЛОВИМ ПРОСТО ТЕКСТ
@dp.message(F.text)
async def handle_text_post(message: Message):
    await message.reply("✅ Ваша новость отправлена на модерацию!")
    await bot.send_message(
        chat_id=ADMIN_ID,
        text=f"<b>Новая предложка:</b>\n\n{message.html_text}",
        reply_markup=get_admin_keyboard(message.from_user.id, message.message_id)
    )


# 2. ЕСЛИ НАЖАЛИ «ОПУБЛИКОВАТЬ»
@dp.callback_query(F.data.startswith("appr:"))
async def approve_post(callback: CallbackQuery):
    # Достаем ID автора и ID его исходного сообщения
    _, user_id, user_msg_id = callback.data.split(":")
    user_id = int(user_id)
    user_msg_id = int(user_msg_id)

    # Публикация фото
    if callback.message.photo:
        original_caption = callback.message.html_text.replace("<b>Новая предложка:</b>\n\n", "")
        final_caption = original_caption + SIGNATURE
        await bot.send_photo(
            chat_id=CHANNEL_ID,
            photo=callback.message.photo[-1].file_id,
            caption=final_caption
        )
        await callback.message.edit_caption(caption="<i>✅ Опубликовано в канал!</i>")
    
    # Публикация просто текста
    elif callback.message.text:
        original_text = callback.message.html_text.replace("<b>Новая предложка:</b>\n\n", "")
        final_text = original_text + SIGNATURE
        await bot.send_message(
            chat_id=CHANNEL_ID,
            text=final_text
        )
        await callback.message.edit_text(text="<i>✅ Опубликовано в канал!</i>")

    # Уведомляем автора новости
    try:
        await bot.send_message(
            chat_id=user_id,
            text="🎉 <b>Ваша новость опубликована в канале!</b>",
            reply_to_message_id=user_msg_id
        )
    except Exception:
        pass  # Если пользователь заблокировал бота, бот не упадет с ошибкой
        
    await callback.answer()


# 3. ЕСЛИ НАЖАЛИ «ОТКЛОНИТЬ»
@dp.callback_query(F.data.startswith("rejl:"))
async def reject_post(callback: CallbackQuery):
    _, user_id, user_msg_id = callback.data.split(":")
    user_id = int(user_id)
    user_msg_id = int(user_msg_id)

    # Меняем сообщение у админа
    if callback.message.photo:
        await callback.message.edit_caption(caption="<i>❌ Отклонено</i>")
    elif callback.message.text:
        await callback.message.edit_text(text="<i>❌ Отклонено</i>")

    # Уведомляем автора новости
    try:
        await bot.send_message(
            chat_id=user_id,
            text="😔 <b>К сожалению, ваша новость отклонена модератором.</b>",
            reply_to_message_id=user_msg_id
        )
    except Exception:
        pass
        
    await callback.answer()


# === ЖЕЛЕЗОБЕТОННЫЙ ОБХОД RENDER ===

web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "Бот работает, всё отлично!"

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    web_app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    Thread(target=run_web_server).start()
    print("Бот успешно запущен!")
    asyncio.run(dp.start_polling(bot))