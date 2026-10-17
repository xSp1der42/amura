import asyncio
import os
from threading import Thread
from dotenv import load_dotenv
from flask import Flask

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

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

# Кнопки
keyboard_admin = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="✅ Опубликовать", callback_data="approve")],
    [InlineKeyboardButton(text="❌ Отклонить", callback_data="reject")]
])


# 1. ЛОВИМ ФОТО С ТЕКСТОМ
@dp.message(F.photo)
async def handle_photo_post(message: Message):
    await message.reply("Ваша новость отправлена на модерацию!")
    caption = message.html_text if message.html_text else ""
    await bot.send_photo(
        chat_id=ADMIN_ID,
        photo=message.photo[-1].file_id,
        caption=f"<b>Новая предложка:</b>\n\n{caption}",
        reply_markup=keyboard_admin
    )


# 2. ОПУБЛИКОВАТЬ
@dp.callback_query(F.data == "approve")
async def approve_post(callback: CallbackQuery):
    original_caption = callback.message.html_text.replace("<b>Новая предложка:</b>\n\n", "")
    final_caption = original_caption + SIGNATURE
    
    await bot.send_photo(
        chat_id=CHANNEL_ID,
        photo=callback.message.photo[-1].file_id,
        caption=final_caption
    )
    await callback.message.edit_caption(caption="<i>✅ Опубликовано в канал!</i>")
    await callback.answer()


# 3. ОТКЛОНИТЬ
@dp.callback_query(F.data == "reject")
async def reject_post(callback: CallbackQuery):
    await callback.message.edit_caption(caption="<i>❌ Отклонено</i>")
    await callback.answer()


# === ЖЕЛЕЗОБЕТОННЫЙ ОБХОД RENDER ===

# Создаем простейший веб-сервер
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "Бот работает, всё отлично!"

def run_web_server():
    # Render сам передает нужный порт через переменную PORT
    port = int(os.environ.get("PORT", 10000))
    # Запускаем сервер
    web_app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    # Запускаем веб-сервер в отдельном потоке, чтобы он сразу открыл порт
    Thread(target=run_web_server).start()
    
    # Запускаем самого бота
    print("Бот успешно запущен!")
    asyncio.run(dp.start_polling(bot))