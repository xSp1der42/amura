import asyncio
import os
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

# Загружаем данные из файла .env
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
CHANNEL_ID = os.getenv("CHANNEL_ID")
CHAT_LINK = os.getenv("CHAT_LINK")
BOT_LINK = os.getenv("BOT_LINK")

# Формируем ту самую подпись
SIGNATURE = f"\n\n<a href='{CHAT_LINK}'>✅ Наш чат</a>\n<a href='{BOT_LINK}'>✅ Предложить новость</a>"

# Инициализируем бота и диспетчер
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# Кнопки для админа
keyboard_admin = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="✅ Опубликовать", callback_data="approve")],
    [InlineKeyboardButton(text="❌ Отклонить", callback_data="reject")]
])


# 1. ЛОВИМ ФОТО С ТЕКСТОМ ОТ ПОЛЬЗОВАТЕЛЕЙ
@dp.message(F.photo)
async def handle_photo_post(message: Message):
    # Отправляем сообщение автору
    await message.reply("Ваша новость отправлена на модерацию!")
    
    # Берем оригинальный текст пользователя (если он есть)
    caption = message.html_text if message.html_text else ""
    
    # Пересылаем фото админу с кнопками
    await bot.send_photo(
        chat_id=ADMIN_ID,
        photo=message.photo[-1].file_id, # Берем фото в лучшем качестве
        caption=f"<b>Новая предложка:</b>\n\n{caption}",
        reply_markup=keyboard_admin
    )


# 2. ЕСЛИ АДМИН НАЖАЛ "ОПУБЛИКОВАТЬ"
@dp.callback_query(F.data == "approve")
async def approve_post(callback: CallbackQuery):
    # Вытаскиваем текст, который пришел админу, но убираем приписку "Новая предложка:"
    # Если это сложно, можно просто брать callback.message.html_text
    original_caption = callback.message.html_text.replace("<b>Новая предложка:</b>\n\n", "")
    
    # ПРИКЛЕИВАЕМ НАШУ ФИРМЕННУЮ ПОДПИСЬ
    final_caption = original_caption + SIGNATURE
    
    # Отправляем в основной канал
    await bot.send_photo(
        chat_id=CHANNEL_ID,
        photo=callback.message.photo[-1].file_id,
        caption=final_caption
    )
    
    # Меняем сообщение у админа (убираем кнопки)
    await callback.message.edit_caption(
        caption="<i>✅ Опубликовано в канал!</i>"
    )
    await callback.answer()


# 3. ЕСЛИ АДМИН НАЖАЛ "ОТКЛОНИТЬ"
@dp.callback_query(F.data == "reject")
async def reject_post(callback: CallbackQuery):
    # Просто убираем кнопки и пишем, что отклонено
    await callback.message.edit_caption(
        caption="<i>❌ Отклонено</i>"
    )
    await callback.answer()


# Запуск бота
async def main():
    print("Бот успешно запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())