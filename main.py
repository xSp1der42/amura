import asyncio
import os
from threading import Thread
from dotenv import load_dotenv
from flask import Flask

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import CommandStart  # <--- Добавили фильтр для команды /start

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
    await bot.send_photo(
        chat_id=ADMIN_ID,
        photo=message.photo[-1].file_id,
        caption=f"<b>Новая предложка:</b>\n\n{caption}",
        reply_markup=keyboard_admin
    )


# 1.1 ЛОВИМ ПРОСТО ТЕКСТ (если прислали без фото)
@dp.message(F.text)
async def handle_text_post(message: Message):
    await message.reply("✅ Ваша новость отправлена на модерацию!")
    await bot.send_message(
        chat_id=ADMIN_ID,
        text=f"<b>Новая предложка:</b>\n\n{message.html_text}",
        reply_markup=keyboard_admin
    )


# 2. ОПУБЛИКОВАТЬ (работает и для фото, и для текста)
@dp.callback_query(F.data == "approve")
async def approve_post(callback: CallbackQuery):
    # Если это фото
    if callback.message.photo:
        original_caption = callback.message.html_text.replace("<b>Новая предложка:</b>\n\n", "")
        final_caption = original_caption + SIGNATURE
        await bot.send_photo(
            chat_id=CHANNEL_ID,
            photo=callback.message.photo[-1].file_id,
            caption=final_caption
        )
        await callback.message.edit_caption(caption="<i>✅ Опубликовано в канал!</i>")
    
    # Если это просто текст
    elif callback.message.text:
        original_text = callback.message.html_text.replace("<b>Новая предложка:</b>\n\n", "")
        final_text = original_text + SIGNATURE
        await bot.send_message(
            chat_id=CHANNEL_ID,
            text=final_text
        )
        await callback.message.edit_text(text="<i>✅ Опубликовано в канал!</i>")
        
    await callback.answer()


# 3. ОТКЛОНИТЬ
@dp.callback_query(F.data == "reject")
async def reject_post(callback: CallbackQuery):
    if callback.message.photo:
        await callback.message.edit_caption(caption="<i>❌ Отклонено</i>")
    elif callback.message.text:
        await callback.message.edit_text(text="<i>❌ Отклонено</i>")
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