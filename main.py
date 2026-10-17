# Импортируем встроенную библиотеку для асинхронного программирования (нужна для работы aiogram 3)
import asyncio
# Импортируем модуль os для работы с операционной системой (чтобы читать переменные окружения)
import os
# Импортируем Thread для запуска процессов параллельно (чтобы веб-сервер и бот работали одновременно)
from threading import Thread
# Импортируем функцию для загрузки переменных из файла .env (чтобы скрыть токены)
from dotenv import load_dotenv
# Импортируем Flask для создания простенького веб-сервера (нужно для хостинга Render)
from flask import Flask

# Импортируем основные классы из библиотеки aiogram для создания бота
from aiogram import Bot, Dispatcher, F
# Импортируем типы данных Telegram + LinkPreviewOptions для отключения огромных плашек со ссылками
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, LinkPreviewOptions
# Импортируем ParseMode для указания того, что мы используем HTML разметку (жирный текст, ссылки и т.д.)
from aiogram.enums import ParseMode
# Импортируем настройки бота по умолчанию (чтобы применить HTML ко всем сообщениям)
from aiogram.client.default import DefaultBotProperties
# Импортируем фильтр для обработки команды /start
from aiogram.filters import CommandStart

# Загружаем данные из файла .env в переменные окружения системы
load_dotenv()

# Достаем токен бота (строка)
BOT_TOKEN = os.getenv("BOT_TOKEN")
# Достаем ID админа и сразу переводим в целое число (int), так как Telegram ID - это числа
ADMIN_ID = int(os.getenv("ADMIN_ID"))
# Достаем ID канала (строка, обычно начинается с минуса, например -10012345678)
CHANNEL_ID = os.getenv("CHANNEL_ID")
# Достаем ссылку на самого бота (строка)
BOT_LINK = os.getenv("BOT_LINK")

# Формируем подпись, которая будет автоматически добавляться к каждому опубликованному посту.
# Тег <a> создает ссылку, а тег <b> делает текст внутри него ЖИРНЫМ.
SIGNATURE = f"\n\n<b><a href='https://t.me/kaza1n'>✅ Ищу тебя Казань</a></b>\n<b><a href='{BOT_LINK}'>✅ Предложить новость</a></b>"

# Инициализируем объект бота. Передаем ему токен и указываем, что по умолчанию весь текст будет в HTML.
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
# Инициализируем диспетчер. Это "маршрутизатор", который ловит все сообщения и передает их нужным функциям.
dp = Dispatcher()


# Функция генерации кнопок для админа.
# Принимает ID пользователя (автора) и ID его сообщения, чтобы знать, кого уведомлять.
def get_admin_keyboard(user_id: int, message_id: int) -> InlineKeyboardMarkup:
    # Возвращаем объект инлайн-клавиатуры (кнопки, которые висят прямо под сообщением)
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            # Кнопка "Опубликовать". В callback_data (то, что отправляется боту при нажатии) 
            # мы "зашиваем" команду 'appr', ID юзера и ID сообщения, разделяя их двоеточием.
            InlineKeyboardButton(text="✅ Опубликовать", callback_data=f"appr:{user_id}:{message_id}"),
            # Кнопка "Отклонить". В callback_data зашиваем команду 'rejl', ID юзера и ID сообщения.
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"rejl:{user_id}:{message_id}")
        ]
    ])


# === 0. ОБРАБОТКА КОМАНДЫ /start ===
# Декоратор, который говорит диспетчеру: "Если придет команда /start, запусти эту функцию"
@dp.message(CommandStart())
async def cmd_start(message: Message):
    # Формируем приветственный текст (<b>...</b> делает текст жирным)
    welcome_text = (
        "👋 Привет!\n\n"
        "Это бот предложки для: <b>Ищу тебя Казань</b>\n"
        "Отправь свое сообщение (фото с текстом или просто текст), и мы опубликуем его в наш канал"
    )
    # Отправляем этот текст пользователю в ответ на /start
    await message.answer(welcome_text)


# === 1. ЛОВИМ ФОТО С ТЕКСТОМ ===
# Декоратор, который ловит сообщения, в которых есть фотография (F.photo)
@dp.message(F.photo)
async def handle_photo_post(message: Message):
    # Отвечаем пользователю, что всё ок
    await message.reply("✅ Ваша новость отправлена на модерацию!")
    
    # Берем подпись к фото вместе с её HTML-разметкой (жирность, курсив). 
    # Если подписи нет, берем пустую строку ("")
    caption = message.html_text if message.html_text else ""
    
    # Отправляем фото админу
    await bot.send_photo(
        chat_id=ADMIN_ID, # Кому отправляем (админу)
        photo=message.photo[-1].file_id, # Берем самую качественную версию фото (последнюю в массиве -1)
        caption=f"<b>Новая предложка:</b>\n\n{caption}", # Добавляем сверху пометку "Новая предложка"
        # Прикрепляем клавиатуру, передавая ID отправителя и ID исходного сообщения
        reply_markup=get_admin_keyboard(message.from_user.id, message.message_id)
    )


# === 1.1 ЛОВИМ ПРОСТО ТЕКСТ ===
# Декоратор, который ловит обычные текстовые сообщения (F.text)
@dp.message(F.text)
async def handle_text_post(message: Message):
    # Отвечаем пользователю
    await message.reply("✅ Ваша новость отправлена на модерацию!")
    
    # Отправляем текст админу
    await bot.send_message(
        chat_id=ADMIN_ID, # Кому отправляем
        text=f"<b>Новая предложка:</b>\n\n{message.html_text}", # Берем текст с сохранением HTML разметки пользователя
        # Прикрепляем клавиатуру
        reply_markup=get_admin_keyboard(message.from_user.id, message.message_id)
    )


# === 2. ЕСЛИ НАЖАЛИ «ОПУБЛИКОВАТЬ» ===
# Декоратор, который ловит нажатие инлайн-кнопки (CallbackQuery), 
# у которой данные начинаются на "appr:" (approve - одобрить)
@dp.callback_query(F.data.startswith("appr:"))
async def approve_post(callback: CallbackQuery):
    # Разбиваем строку "appr:12345:678" по двоеточию на три части.
    # Первую (appr) игнорируем (через символ '_'), вторую сохраняем как user_id, третью как user_msg_id
    _, user_id, user_msg_id = callback.data.split(":")
    
    # Переводим полученные ID из строк обратно в числа
    user_id = int(user_id)
    user_msg_id = int(user_msg_id)

    # Проверяем, есть ли в сообщении, под которым нажали кнопку, фотография
    if callback.message.photo:
        # Убираем пометку "Новая предложка:", чтобы выложить в канал чистый текст
        original_caption = callback.message.html_text.replace("<b>Новая предложка:</b>\n\n", "")
        # Приклеиваем к чистому тексту нашу постоянную подпись (ссылки)
        final_caption = original_caption + SIGNATURE
        
        # Отправляем итоговое фото с текстом в основной канал
        await bot.send_photo(
            chat_id=CHANNEL_ID,
            photo=callback.message.photo[-1].file_id,
            caption=final_caption
        )
        # Изменяем сообщение у админа: убираем кнопки и пишем "Опубликовано", чтобы не нажать дважды
        await callback.message.edit_caption(caption="<i>✅ Опубликовано в канал!</i>")
    
    # Проверяем, если это был просто текст (без фото)
    elif callback.message.text:
        # Убираем техническую пометку
        original_text = callback.message.html_text.replace("<b>Новая предложка:</b>\n\n", "")
        # Приклеиваем подпись
        final_text = original_text + SIGNATURE
        
        # Отправляем в канал текстовое сообщение и ОТКЛЮЧАЕМ ПРЕВЬЮ ССЫЛОК
        await bot.send_message(
            chat_id=CHANNEL_ID,
            text=final_text,
            link_preview_options=LinkPreviewOptions(is_disabled=True)
        )
        # Меняем текст у админа, убирая кнопки
        await callback.message.edit_text(text="<i>✅ Опубликовано в канал!</i>")

    # Уведомляем автора новости о том, что его пост вышел
    try:
        await bot.send_message(
            chat_id=user_id, # Кому (автору)
            text="🎉 <b>Ваша новость опубликована в канале!</b>",
            reply_to_message_id=user_msg_id # Делаем это реплаем (ответом) на его исходное сообщение
        )
    except Exception:
        # Если блок try выдаст ошибку (например, пользователь заблокировал бота), 
        # программа перейдет сюда. pass означает "ничего не делать, проигнорировать".
        # Бот не упадет с ошибкой.
        pass 
        
    # Обязательно "отвечаем" на коллбэк, чтобы у админа на кнопке пропали "часики" загрузки
    await callback.answer()


# === 3. ЕСЛИ НАЖАЛИ «ОТКЛОНИТЬ» ===
# Ловим нажатие кнопок, данные которых начинаются на "rejl:" (reject - отклонить)
@dp.callback_query(F.data.startswith("rejl:"))
async def reject_post(callback: CallbackQuery):
    # Достаем ID пользователя и сообщения точно так же, как при публикации
    _, user_id, user_msg_id = callback.data.split(":")
    user_id = int(user_id)
    user_msg_id = int(user_msg_id)

    # Меняем сообщение у админа, чтобы он видел, что пост отклонен (и кнопки пропали)
    if callback.message.photo:
        await callback.message.edit_caption(caption="<i>❌ Отклонено</i>")
    elif callback.message.text:
        await callback.message.edit_text(text="<i>❌ Отклонено</i>")

    # Пытаемся уведомить автора новости об отказе
    try:
        await bot.send_message(
            chat_id=user_id,
            text="😔 <b>К сожалению, ваша новость отклонена модератором.</b>",
            reply_to_message_id=user_msg_id # Снова отвечаем на его же сообщение
        )
    except Exception:
        # Игнорируем ошибку, если автор заблокировал бота
        pass
        
    # Убираем "часики" загрузки на кнопке у админа
    await callback.answer()


# === ЖЕЛЕЗОБЕТОННЫЙ ОБХОД RENDER ===
# Сервисы вроде Render требуют, чтобы приложение открывало веб-порт, иначе они его "убивают", думая, что оно зависло.
# Поэтому мы создаем фейковый веб-сервер.

# Инициализируем приложение Flask
web_app = Flask(__name__)

# Говорим Flask, что если кто-то зайдет на главную страницу (корень '/'), нужно вернуть этот текст
@web_app.route('/')
def home():
    return "Бот работает, всё отлично!"

# Функция, которая запускает наш Flask-сервер
def run_web_server():
    # Получаем порт из переменных окружения (Render сам выдаст нужный). Если его нет - используем 10000.
    port = int(os.environ.get("PORT", 10000))
    # Запускаем сервер на всех IP-адресах (0.0.0.0) на указанном порту
    web_app.run(host="0.0.0.0", port=port)

# Эта конструкция означает: "Если этот файл запустили напрямую (а не импортировали в другой файл), то сделай следующее:"
if __name__ == "__main__":
    # Запускаем веб-сервер в отдельном потоке (Thread). 
    # Если запустить его обычно, он заблокирует программу, и бот не включится.
    # Благодаря Thread, веб-сервер работает на фоне.
    Thread(target=run_web_server).start()
    
    # Выводим в консоль техническое сообщение для нас
    print("Бот успешно запущен!")
    
    # Запускаем самого бота. start_polling означает, что бот будет постоянно спрашивать сервера Telegram: 
    # "Мне есть новые сообщения?". asyncio.run запускает асинхронный процесс.
    asyncio.run(dp.start_polling(bot))