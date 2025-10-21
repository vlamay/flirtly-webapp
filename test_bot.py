# test_bot.py - Упрощенный бот для тестирования команд

import asyncio
import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфигурация
BOT_TOKEN = "8430527446:AAFLoCZqvreDpsgz4d5z4J5LXMLC42B9ex0"
WEBAPP_URL = "https://vlamay.github.io/flirtly-webapp"

class TestBot:
    def __init__(self):
        self.app = Application.builder().token(BOT_TOKEN).build()
        self._register_handlers()
    
    def _register_handlers(self):
        """Регистрация обработчиков"""
        # Commands
        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(CommandHandler("profile", self.profile))
        self.app.add_handler(CommandHandler("matches", self.matches))
        self.app.add_handler(CommandHandler("search", self.search))
        self.app.add_handler(CommandHandler("premium", self.premium))
        self.app.add_handler(CommandHandler("settings", self.settings))
        self.app.add_handler(CommandHandler("help", self.help))
        
        # Callback queries
        self.app.add_handler(CallbackQueryHandler(self.handle_callback))
        
        # Messages
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
    
    async def start(self, update: Update, context):
        """Команда /start"""
        user = update.effective_user
        logger.info(f"User {user.id} ({user.username}) used /start")
        
        keyboard = [
            [InlineKeyboardButton(
                "⚡ Открыть Flirtly", 
                web_app=WebAppInfo(url=WEBAPP_URL)
            )],
            [
                InlineKeyboardButton("👤 Мой профиль", callback_data="profile"),
                InlineKeyboardButton("💕 Мои матчи", callback_data="matches")
            ],
            [
                InlineKeyboardButton("🔍 Искать", callback_data="search"),
                InlineKeyboardButton("💬 Чаты", callback_data="chats")
            ],
            [
                InlineKeyboardButton("⭐ Premium", callback_data="premium"),
                InlineKeyboardButton("⚙️ Настройки", callback_data="settings")
            ],
            [InlineKeyboardButton("🎁 Пригласить друзей", callback_data="referral")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"🔥 <b>Привет, {user.first_name}!</b>\n\n"
            f"Добро пожаловать в <b>Flirtly</b> ⚡ - знакомства нового уровня!\n\n"
            f"<b>Что тебя ждет:</b>\n"
            f"• 💕 Умный подбор совпадений\n"
            f"• ⚡ Swipe как в популярных приложениях\n"
            f"• 💬 Общение прямо в Telegram\n"
            f"• 🎁 Бонусы за приглашения друзей\n\n"
            f"<b>Нажми кнопку ниже чтобы начать!</b>",
            parse_mode='HTML',
            reply_markup=reply_markup
        )
    
    async def profile(self, update: Update, context):
        """Команда /profile"""
        user = update.effective_user
        logger.info(f"User {user.id} used /profile")
        
        profile_text = f"""
👤 <b>Твой профиль</b>

<b>Основная информация:</b>
• Имя: {user.first_name or 'Не указано'}
• Username: @{user.username or 'Не указан'}
• ID: {user.id}

<b>Статистика:</b>
• ❤️ Лайков отправлено: 5
• 💕 Получено лайков: 12
• 🎯 Совпадений: 3
• 📸 Фото: 2

<b>Подписка:</b>
• Статус: 🆓 Бесплатная
        """
        
        keyboard = [
            [InlineKeyboardButton("✏️ Редактировать", 
                                web_app=WebAppInfo(url=f"{WEBAPP_URL}/profile"))],
            [InlineKeyboardButton("📸 Добавить фото", callback_data="add_photo")],
            [InlineKeyboardButton("◀️ Назад", callback_data="back_to_start")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            profile_text,
            parse_mode='HTML',
            reply_markup=reply_markup
        )
    
    async def matches(self, update: Update, context):
        """Команда /matches"""
        user = update.effective_user
        logger.info(f"User {user.id} used /matches")
        
        matches_text = """
💕 <b>Мои совпадения</b>

1. <b>Анна, 25</b> • Москва
2. <b>Мария, 26</b> • Санкт-Петербург  
3. <b>Елена, 24</b> • Казань

<b>У тебя 3 активных совпадения!</b>
        """
        
        keyboard = [
            [InlineKeyboardButton("💬 Чат с Анной", callback_data="chat_1")],
            [InlineKeyboardButton("💬 Чат с Марией", callback_data="chat_2")],
            [InlineKeyboardButton("💬 Чат с Еленой", callback_data="chat_3")],
            [InlineKeyboardButton("👀 Все совпадения", 
                                web_app=WebAppInfo(url=f"{WEBAPP_URL}/matches"))],
            [InlineKeyboardButton("◀️ Назад", callback_data="back_to_start")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            matches_text,
            parse_mode='HTML',
            reply_markup=reply_markup
        )
    
    async def search(self, update: Update, context):
        """Команда /search"""
        user = update.effective_user
        logger.info(f"User {user.id} used /search")
        
        search_text = """
🔍 <b>Поиск анкет</b>

<b>Готов искать новые знакомства!</b>

<b>Твои настройки:</b>
• Возраст: 18-35
• Пол: Женщины
• Расстояние: 50 км

<b>Лайков осталось: 5</b>

<b>Начни свайпать прямо сейчас!</b>
        """
        
        keyboard = [
            [InlineKeyboardButton("⚡ Начать свайпать", 
                                web_app=WebAppInfo(url=WEBAPP_URL))],
            [InlineKeyboardButton("⚙️ Настроить фильтры", callback_data="filters")],
            [InlineKeyboardButton("◀️ Назад", callback_data="back_to_start")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            search_text,
            parse_mode='HTML',
            reply_markup=reply_markup
        )
    
    async def premium(self, update: Update, context):
        """Команда /premium"""
        user = update.effective_user
        logger.info(f"User {user.id} used /premium")
        
        premium_text = """
⭐ <b>Premium подписка</b>

<b>🌟 PREMIUM (250 ⭐/месяц)</b>
• Безлимитные лайки ❤️
• 5 суперлайков в день ⚡
• Расширенные фильтры 🔍
• Видеть кто лайкнул 👀
• Приоритет в показе 📊

<b>💎 PLATINUM (500 ⭐/месяц)</b>
• Всё из Premium +
• AI совместимость 🤖
• Инкогнито режим 👻
• Видеть все просмотры 👁️
• Персональные рекомендации 🎯

<b>💳 Telegram Stars</b>
Оплата через Telegram Stars - быстро и безопасно!

<b>Специальное предложение:</b>
• Первая неделя Premium - БЕСПЛАТНО! 🎁
• При оплате на месяц - скидка 20% 💰
        """
        
        keyboard = [
            [InlineKeyboardButton("⭐ Купить Premium", 
                                web_app=WebAppInfo(url=f"{WEBAPP_URL}/premium"))],
            [InlineKeyboardButton("💎 Купить Platinum", 
                                web_app=WebAppInfo(url=f"{WEBAPP_URL}/premium"))],
            [InlineKeyboardButton("🎁 Попробовать бесплатно", callback_data="free_trial")],
            [InlineKeyboardButton("◀️ Назад", callback_data="back_to_start")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            premium_text,
            parse_mode='HTML',
            reply_markup=reply_markup
        )
    
    async def settings(self, update: Update, context):
        """Команда /settings"""
        user = update.effective_user
        logger.info(f"User {user.id} used /settings")
        
        settings_text = """
⚙️ <b>Настройки</b>

<b>Уведомления:</b>
• Новые матчи: ✅
• Сообщения: ✅
• Лайки: ✅
• Premium предложения: ❌

<b>Приватность:</b>
• Показывать в поиске: ✅
• Показывать расстояние: ✅
• Показывать последнюю активность: ✅

<b>Фильтры:</b>
• Возраст: 18-99
• Расстояние: 50 км
• Только с фото: ❌
        """
        
        keyboard = [
            [InlineKeyboardButton("🔔 Уведомления", callback_data="notifications")],
            [InlineKeyboardButton("🔒 Приватность", callback_data="privacy")],
            [InlineKeyboardButton("🔍 Фильтры", callback_data="filters")],
            [InlineKeyboardButton("📱 Управление через Web App", 
                                web_app=WebAppInfo(url=f"{WEBAPP_URL}/settings"))],
            [InlineKeyboardButton("◀️ Назад", callback_data="back_to_start")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            settings_text,
            parse_mode='HTML',
            reply_markup=reply_markup
        )
    
    async def help(self, update: Update, context):
        """Команда /help"""
        user = update.effective_user
        logger.info(f"User {user.id} used /help")
        
        help_text = """
ℹ️ <b>Помощь</b>

<b>Основные команды:</b>
/start - Главное меню
/profile - Мой профиль
/matches - Мои совпадения
/search - Поиск анкет
/premium - Premium подписка
/settings - Настройки
/help - Эта справка

<b>Как пользоваться:</b>
1. Зарегистрируйся через Web App
2. Заполни профиль и добавь фото
3. Начни свайпать анкеты
4. Получай совпадения и общайся!

<b>Проблемы с фото?</b>
• Используй качественные фото
• Покажи лицо на первом фото
• Добавь 3-6 фото для лучших результатов

<b>Нужна помощь?</b>
• 📧 Напиши @support
• 💬 Группа поддержки: @flirtly_support
• 🌐 Сайт: https://flirtly.app
        """
        
        keyboard = [
            [InlineKeyboardButton("⚡ Открыть Web App", 
                                web_app=WebAppInfo(url=WEBAPP_URL))],
            [InlineKeyboardButton("📧 Поддержка", url="https://t.me/support")],
            [InlineKeyboardButton("💬 Группа", url="https://t.me/flirtly_support")],
            [InlineKeyboardButton("◀️ Назад", callback_data="back_to_start")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            help_text,
            parse_mode='HTML',
            reply_markup=reply_markup
        )
    
    async def handle_callback(self, update: Update, context):
        """Обработка inline кнопок"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        user_id = query.from_user.id
        
        logger.info(f"User {user_id} clicked button: {data}")
        
        if data == "back_to_start":
            await self.start(update, context)
        
        elif data == "profile":
            await self.profile(update, context)
        
        elif data == "matches":
            await self.matches(update, context)
        
        elif data == "search":
            await self.search(update, context)
        
        elif data == "premium":
            await self.premium(update, context)
        
        elif data == "settings":
            await self.settings(update, context)
        
        elif data.startswith("chat_"):
            match_id = data.split("_")[1]
            await query.edit_message_text(
                f"💬 <b>Чат с пользователем {match_id}</b>\n\n"
                f"Открой Web App для удобного общения!",
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⚡ Открыть чат", 
                                       web_app=WebAppInfo(url=f"{WEBAPP_URL}/chat/{match_id}"))
                ]])
            )
        
        elif data == "referral":
            user_id = query.from_user.id
            ref_link = f"https://t.me/FFlirtly_bot?start=ref_{user_id}"
            
            await query.edit_message_text(
                f"🎁 <b>Реферальная программа</b>\n\n"
                f"Приглашай друзей и получай бонусы!\n\n"
                f"<b>За каждого друга:</b>\n"
                f"• Ты получаешь: +10 лайков\n"
                f"• Друг получает: +5 лайков\n\n"
                f"<b>Твоя ссылка:</b>\n"
                f"<code>{ref_link}</code>\n\n"
                f"Нажми кнопку чтобы поделиться!",
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📤 Поделиться", 
                                       url=f"https://t.me/share/url?url={ref_link}&text=🔥 Попробуй Flirtly!")],
                    [InlineKeyboardButton("◀️ Назад", callback_data="back_to_start")]
                ])
            )
        
        elif data == "free_trial":
            await query.edit_message_text(
                "🎁 <b>Бесплатная неделя Premium активирована!</b>\n\n"
                "Ты получил доступ ко всем Premium функциям на 7 дней:\n"
                "• Безлимитные лайки ❤️\n"
                "• 5 суперлайков в день ⚡\n"
                "• Расширенные фильтры 🔍\n"
                "• Видеть кто лайкнул 👀\n\n"
                "Наслаждайся Premium опытом!",
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⚡ Начать использовать", 
                                       web_app=WebAppInfo(url=WEBAPP_URL))
                ]])
            )
        
        else:
            await query.edit_message_text(
                f"🔧 <b>Функция в разработке</b>\n\n"
                f"Кнопка '{data}' пока не реализована.\n"
                f"Используй Web App для полного функционала!",
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⚡ Открыть Web App", 
                                       web_app=WebAppInfo(url=WEBAPP_URL))
                ]])
            )
    
    async def handle_message(self, update: Update, context):
        """Обработка сообщений"""
        user = update.effective_user
        message_text = update.message.text
        
        logger.info(f"User {user.id} sent message: {message_text}")
        
        await update.message.reply_text(
            "💬 <b>Привет!</b>\n\n"
            "Я бот для знакомств Flirtly! Используй команды:\n\n"
            "/start - Главное меню\n"
            "/profile - Мой профиль\n"
            "/matches - Мои совпадения\n"
            "/search - Поиск анкет\n"
            "/premium - Premium подписка\n"
            "/help - Помощь\n\n"
            "Или открой Web App для полного функционала!",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("⚡ Открыть Web App", 
                                   web_app=WebAppInfo(url=WEBAPP_URL))
            ]])
        )
    
    def run(self):
        """Запуск бота"""
        logger.info("Starting Test Bot...")
        self.app.run_polling()

if __name__ == "__main__":
    bot = TestBot()
    bot.run()
