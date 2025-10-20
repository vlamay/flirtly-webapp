# bot_simple.py - Упрощенная версия Telegram бота

import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Токен бота
BOT_TOKEN = "8430527446:AAFLoCZqvreDpsgz4d5z4J5LXMLC42B9ex0"
WEBAPP_URL = "https://vlamay.github.io/flirtly-webapp/"

# Инициализация
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


def get_main_keyboard() -> InlineKeyboardMarkup:
    """Главная клавиатура"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="⚡ Открыть Flirtly",
                web_app=WebAppInfo(url=WEBAPP_URL)
            )
        ],
        [
            InlineKeyboardButton(text="ℹ️ О сервисе", callback_data="about"),
            InlineKeyboardButton(text="🎁 Пригласить", callback_data="referral")
        ],
        [
            InlineKeyboardButton(text="⭐ Premium", callback_data="premium"),
            InlineKeyboardButton(text="❓ Помощь", callback_data="help")
        ]
    ])


@dp.message(Command("start"))
async def cmd_start(message: Message):
    """Команда /start"""
    user_name = message.from_user.first_name
    
    # Проверяем реферальную ссылку
    args = message.text.split()
    referrer_text = ""
    if len(args) > 1 and args[1].startswith("ref_"):
        referrer_text = "\n\n🎁 <b>Ты получишь +5 лайков от друга!</b>"
    
    await message.answer(
        f"<b>Привет, {user_name}! 👋</b>\n\n"
        f"Добро пожаловать в <b>Flirtly</b> ⚡\n\n"
        f"Современный сервис знакомств прямо в Telegram!\n\n"
        f"<b>Что тебя ждет:</b>\n"
        f"• 💕 Умный подбор совпадений\n"
        f"• ⚡ Swipe как в популярных приложениях\n"
        f"• 💬 Instant чат с совпадениями\n"
        f"• 🎁 Бонусы за приглашения\n\n"
        f"{referrer_text}\n\n"
        f"<b>Нажми кнопку ниже чтобы начать!</b>",
        parse_mode="HTML",
        reply_markup=get_main_keyboard()
    )


@dp.message(Command("profile"))
async def cmd_profile(message: Message):
    """Команда /profile"""
    await message.answer(
        "👤 <b>Твой профиль</b>\n\n"
        "Открой Web App чтобы управлять профилем!",
        parse_mode="HTML",
        reply_markup=get_main_keyboard()
    )


@dp.message(Command("search"))
async def cmd_search(message: Message):
    """Команда /search"""
    await message.answer(
        "🔍 <b>Поиск анкет</b>\n\n"
        "Открой Web App чтобы начать поиск!",
        parse_mode="HTML",
        reply_markup=get_main_keyboard()
    )


@dp.message(Command("matches"))
async def cmd_matches(message: Message):
    """Команда /matches"""
    await message.answer(
        "💕 <b>Твои совпадения</b>\n\n"
        "У тебя пока нет совпадений.\n"
        "Открой Web App и начни свайпать!",
        parse_mode="HTML",
        reply_markup=get_main_keyboard()
    )


@dp.message(Command("chats"))
async def cmd_chats(message: Message):
    """Команда /chats"""
    await message.answer(
        "💬 <b>Твои чаты</b>\n\n"
        "У тебя пока нет чатов.\n"
        "Получи первое совпадение!",
        parse_mode="HTML",
        reply_markup=get_main_keyboard()
    )


@dp.message(Command("premium"))
async def cmd_premium(message: Message):
    """Команда /premium"""
    await message.answer(
        "⭐ <b>Premium подписка</b>\n\n"
        "<b>🌟 PREMIUM (250 ⭐/месяц)</b>\n"
        "• Безлимитные лайки ❤️\n"
        "• 5 суперлайков в день ⚡\n"
        "• Расширенные фильтры 🔍\n"
        "• Видеть кто лайкнул 👀\n\n"
        "<b>💎 PLATINUM (500 ⭐/месяц)</b>\n"
        "• Всё из Premium +\n"
        "• AI совместимость 🤖\n"
        "• Приоритет в показе 📊\n"
        "• Инкогнито режим 👻\n\n"
        "Открой Web App для оформления!",
        parse_mode="HTML",
        reply_markup=get_main_keyboard()
    )


@dp.message(Command("settings"))
async def cmd_settings(message: Message):
    """Команда /settings"""
    await message.answer(
        "⚙️ <b>Настройки</b>\n\n"
        "Управляй настройками через Web App!",
        parse_mode="HTML",
        reply_markup=get_main_keyboard()
    )


@dp.message(Command("help"))
async def cmd_help(message: Message):
    """Команда /help"""
    await message.answer(
        "ℹ️ <b>Помощь</b>\n\n"
        "<b>Доступные команды:</b>\n"
        "/start - Начать работу\n"
        "/profile - Твой профиль\n"
        "/search - Искать анкеты\n"
        "/matches - Твои совпадения\n"
        "/chats - Твои чаты\n"
        "/premium - Premium подписка\n"
        "/settings - Настройки\n"
        "/help - Помощь\n\n"
        "<b>Нужна помощь?</b>\n"
        "Напиши @support",
        parse_mode="HTML",
        reply_markup=get_main_keyboard()
    )


@dp.callback_query(F.data == "about")
async def callback_about(callback):
    """О сервисе"""
    await callback.message.edit_text(
        "<b>О Flirtly</b> ⚡\n\n"
        "Современный сервис знакомств в Telegram!\n\n"
        "<b>Преимущества:</b>\n"
        "• Удобный интерфейс\n"
        "• Безопасность данных\n"
        "• Умный подбор\n"
        "• Instant чат\n\n"
        "<b>Начни знакомиться прямо сейчас!</b>",
        parse_mode="HTML",
        reply_markup=get_main_keyboard()
    )
    await callback.answer()


@dp.callback_query(F.data == "referral")
async def callback_referral(callback):
    """Реферальная программа"""
    user_id = callback.from_user.id
    ref_link = f"https://t.me/FFlirtly_bot?start=ref_{user_id}"
    
    await callback.message.edit_text(
        "🎁 <b>Реферальная программа</b>\n\n"
        "Приглашай друзей и получай бонусы!\n\n"
        "<b>За каждого друга:</b>\n"
        "• Ты получаешь: +10 лайков\n"
        "• Друг получает: +5 лайков\n\n"
        f"<b>Твоя ссылка:</b>\n"
        f"<code>{ref_link}</code>\n\n"
        "Нажми чтобы скопировать!",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📤 Поделиться",
                    url=f"https://t.me/share/url?url={ref_link}&text=🔥 Попробуй Flirtly!"
                )
            ],
            [
                InlineKeyboardButton(text="◀️ Назад", callback_data="back")
            ]
        ])
    )
    await callback.answer()


@dp.callback_query(F.data == "premium")
async def callback_premium(callback):
    """Premium подписка"""
    await callback.message.edit_text(
        "⭐ <b>Premium подписка</b>\n\n"
        "<b>🌟 PREMIUM (250 ⭐/месяц)</b>\n"
        "• Безлимитные лайки\n"
        "• 5 суперлайков/день\n"
        "• Расширенные фильтры\n"
        "• Видеть кто лайкнул\n\n"
        "<b>💎 PLATINUM (500 ⭐/месяц)</b>\n"
        "• Всё из Premium +\n"
        "• AI совместимость\n"
        "• Приоритет в показе\n"
        "• Инкогнито режим\n\n"
        "Оформи через Web App!",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⚡ Открыть Flirtly",
                    web_app=WebAppInfo(url=WEBAPP_URL)
                )
            ],
            [
                InlineKeyboardButton(text="◀️ Назад", callback_data="back")
            ]
        ])
    )
    await callback.answer()


@dp.callback_query(F.data == "help")
async def callback_help(callback):
    """Помощь"""
    await callback.message.edit_text(
        "ℹ️ <b>Помощь</b>\n\n"
        "<b>Как пользоваться:</b>\n"
        "1. Открой Web App\n"
        "2. Заполни профиль\n"
        "3. Начни свайпать анкеты\n"
        "4. Получай совпадения\n"
        "5. Общайся!\n\n"
        "<b>Вопросы?</b>\n"
        "Напиши @support",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="◀️ Назад", callback_data="back")
            ]
        ])
    )
    await callback.answer()


@dp.callback_query(F.data == "back")
async def callback_back(callback):
    """Назад в главное меню"""
    user_name = callback.from_user.first_name
    await callback.message.edit_text(
        f"<b>Привет, {user_name}! 👋</b>\n\n"
        f"Нажми кнопку ниже чтобы открыть Flirtly!",
        parse_mode="HTML",
        reply_markup=get_main_keyboard()
    )
    await callback.answer()


@dp.message(F.web_app_data)
async def handle_webapp_data(message: Message):
    """Обработка данных из Web App"""
    import json
    
    try:
        data = json.loads(message.web_app_data.data)
        action = data.get('action')
        
        if action == 'register':
            name = data.get('name')
            age = data.get('age')
            
            await message.answer(
                f"🎉 <b>Регистрация завершена!</b>\n\n"
                f"Добро пожаловать, {name}, {age} лет!\n\n"
                f"Теперь можешь начать искать совпадения! ⚡",
                parse_mode="HTML"
            )
        
        elif action == 'like':
            await message.answer("❤️ Лайк отправлен!")
        
        elif action == 'superlike':
            await message.answer("⭐ Суперлайк отправлен!")
        
        elif action == 'skip':
            await message.answer("👎 Пропущено")
        
        else:
            await message.answer("✅ Данные получены!")
    
    except Exception as e:
        logger.error(f"Error handling webapp data: {e}")
        await message.answer("❌ Произошла ошибка")


async def main():
    """Запуск бота"""
    logger.info("Starting Flirtly Bot...")
    
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
