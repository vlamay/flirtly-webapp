# bot_full.py - Полноценный Telegram Bot с командами и inline кнопками

import asyncio
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from telegram.constants import ParseMode
from typing import Optional
import os
from datetime import datetime, timedelta

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class FlirtlyBot:
    def __init__(self, token: str, webapp_url: str):
        self.token = token
        self.webapp_url = webapp_url
        self.app = Application.builder().token(token).build()
        self._register_handlers()
    
    def _register_handlers(self):
        """Регистрация всех обработчиков"""
        # Commands
        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(CommandHandler("profile", self.profile))
        self.app.add_handler(CommandHandler("matches", self.matches))
        self.app.add_handler(CommandHandler("search", self.search))
        self.app.add_handler(CommandHandler("settings", self.settings))
        self.app.add_handler(CommandHandler("help", self.help))
        self.app.add_handler(CommandHandler("premium", self.premium))
        
        # Callback queries (inline buttons)
        self.app.add_handler(CallbackQueryHandler(self.handle_callback))
        
        # Messages (для чата между матчами)
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
    
    async def start(self, update: Update, context):
        """Главная команда /start"""
        user = update.effective_user
        logger.info(f"User {user.id} ({user.username}) started the bot")
        
        # Проверяем есть ли пользователь в базе
        user_exists = await self.check_user_exists(user.id)
        
        if not user_exists:
            # Новый пользователь - показываем приветствие
            welcome_text = f"""
🔥 <b>Привет, {user.first_name}!</b>

Добро пожаловать в <b>Flirtly</b> ⚡ - знакомства нового уровня!

<b>Что тебя ждет:</b>
• 💕 Умный подбор совпадений
• ⚡ Swipe как в популярных приложениях  
• 💬 Общение прямо в Telegram
• 🎁 Бонусы за приглашения друзей

<b>Нажми кнопку ниже чтобы начать!</b>
            """
        else:
            # Существующий пользователь
            user_data = await self.get_user_data(user.id)
            welcome_text = f"""
<b>С возвращением, {user_data.get('name', user.first_name)}! 👋</b>

<b>Твоя статистика:</b>
• ❤️ Лайков осталось: {10 - user_data.get('likes_sent', 0)}
• 💕 Совпадений: {user_data.get('matches_count', 0)}
• 💬 Активных чатов: {user_data.get('active_chats', 0)}

<b>Готов искать новые знакомства?</b>
            """
        
        keyboard = [
            [InlineKeyboardButton(
                "⚡ Открыть Flirtly", 
                web_app=WebAppInfo(url=self.webapp_url)
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
            welcome_text,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )
    
    async def profile(self, update: Update, context):
        """Команда /profile"""
        user_id = update.effective_user.id
        user_data = await self.get_user_data(user_id)
        
        if not user_data:
            await update.message.reply_text(
                "❌ Профиль не найден. Сначала зарегистрируйся в Web App!",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⚡ Зарегистрироваться", 
                                       web_app=WebAppInfo(url=self.webapp_url))
                ]])
            )
            return
        
        profile_text = f"""
👤 <b>Твой профиль</b>

<b>Основная информация:</b>
• Имя: {user_data.get('name', 'Не указано')}
• Возраст: {user_data.get('age', 'Не указан')}
• Пол: {user_data.get('gender', 'Не указан')}
• Ищу: {user_data.get('looking_for', 'Не указано')}
• Город: {user_data.get('city', 'Не указан')}

<b>Статистика:</b>
• ❤️ Лайков отправлено: {user_data.get('likes_sent', 0)}
• 💕 Получено лайков: {user_data.get('likes_received', 0)}
• 🎯 Совпадений: {user_data.get('matches_count', 0)}
• 📸 Фото: {len(user_data.get('photos', []))}

<b>Подписка:</b>
• Статус: {'⭐ Premium' if user_data.get('is_premium') else '🆓 Бесплатная'}
• До: {user_data.get('premium_until', 'Не указано')}
        """
        
        keyboard = [
            [InlineKeyboardButton("✏️ Редактировать", 
                                web_app=WebAppInfo(url=f"{self.webapp_url}/profile"))],
            [InlineKeyboardButton("📸 Добавить фото", callback_data="add_photo")],
            [InlineKeyboardButton("◀️ Назад", callback_data="back_to_start")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            profile_text,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )
    
    async def matches(self, update: Update, context):
        """Команда /matches"""
        user_id = update.effective_user.id
        matches = await self.get_user_matches(user_id)
        
        if not matches:
            matches_text = """
💕 <b>Мои совпадения</b>

У тебя пока нет совпадений 😔

<b>Как получить матчи:</b>
• 📸 Добавь качественные фото
• ✍️ Напиши интересную биографию
• 🔍 Активно свайпай анкеты
• ⭐ Купи Premium для больше возможностей

<b>Начни искать прямо сейчас!</b>
            """
            keyboard = [
                [InlineKeyboardButton("⚡ Начать поиск", 
                                    web_app=WebAppInfo(url=self.webapp_url))],
                [InlineKeyboardButton("◀️ Назад", callback_data="back_to_start")]
            ]
        else:
            matches_text = "💕 <b>Мои совпадения</b>\n\n"
            keyboard = []
            
            for i, match in enumerate(matches[:5]):  # Показываем первые 5
                matches_text += f"{i+1}. <b>{match['name']}</b>, {match['age']}\n"
                keyboard.append([InlineKeyboardButton(
                    f"💬 Чат с {match['name']}", 
                    callback_data=f"chat_{match['id']}"
                )])
            
            if len(matches) > 5:
                matches_text += f"\n... и еще {len(matches) - 5} совпадений"
            
            keyboard.extend([
                [InlineKeyboardButton("👀 Все совпадения", 
                                    web_app=WebAppInfo(url=f"{self.webapp_url}/matches"))],
                [InlineKeyboardButton("◀️ Назад", callback_data="back_to_start")]
            ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            matches_text,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )
    
    async def search(self, update: Update, context):
        """Команда /search"""
        user_id = update.effective_user.id
        user_data = await self.get_user_data(user_id)
        
        if not user_data:
            await update.message.reply_text(
                "❌ Сначала зарегистрируйся в Web App!",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⚡ Зарегистрироваться", 
                                       web_app=WebAppInfo(url=self.webapp_url))
                ]])
            )
            return
        
        # Проверяем лимиты
        likes_left = 10 - user_data.get('likes_sent', 0)
        
        if likes_left <= 0:
            search_text = """
🔍 <b>Поиск анкет</b>

❌ У тебя закончились лайки!

<b>Как получить больше лайков:</b>
• ⭐ Купи Premium - безлимитные лайки
• 🎁 Пригласи друзей - получи бонусы
• ⏰ Подожди до завтра - лайки обновятся

<b>Premium подписка:</b>
• Безлимитные лайки ❤️
• 5 суперлайков в день ⚡
• Расширенные фильтры 🔍
• Видеть кто лайкнул 👀
            """
            keyboard = [
                [InlineKeyboardButton("⭐ Купить Premium", callback_data="premium")],
                [InlineKeyboardButton("🎁 Пригласить друзей", callback_data="referral")],
                [InlineKeyboardButton("◀️ Назад", callback_data="back_to_start")]
            ]
        else:
            search_text = f"""
🔍 <b>Поиск анкет</b>

<b>Готов искать новые знакомства!</b>

<b>Твои настройки:</b>
• Возраст: {user_data.get('age_min', 18)}-{user_data.get('age_max', 99)}
• Пол: {user_data.get('looking_for', 'Все')}
• Расстояние: {user_data.get('max_distance', 50)} км

<b>Лайков осталось: {likes_left}</b>

<b>Начни свайпать прямо сейчас!</b>
            """
            keyboard = [
                [InlineKeyboardButton("⚡ Начать свайпать", 
                                    web_app=WebAppInfo(url=self.webapp_url))],
                [InlineKeyboardButton("⚙️ Настроить фильтры", callback_data="filters")],
                [InlineKeyboardButton("◀️ Назад", callback_data="back_to_start")]
            ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            search_text,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )
    
    async def premium(self, update: Update, context):
        """Команда /premium"""
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
                                web_app=WebAppInfo(url=f"{self.webapp_url}/premium"))],
            [InlineKeyboardButton("💎 Купить Platinum", 
                                web_app=WebAppInfo(url=f"{self.webapp_url}/premium"))],
            [InlineKeyboardButton("🎁 Попробовать бесплатно", callback_data="free_trial")],
            [InlineKeyboardButton("◀️ Назад", callback_data="back_to_start")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            premium_text,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )
    
    async def settings(self, update: Update, context):
        """Команда /settings"""
        user_id = update.effective_user.id
        user_data = await self.get_user_data(user_id)
        
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
                                web_app=WebAppInfo(url=f"{self.webapp_url}/settings"))],
            [InlineKeyboardButton("◀️ Назад", callback_data="back_to_start")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            settings_text,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )
    
    async def help(self, update: Update, context):
        """Команда /help"""
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
                                web_app=WebAppInfo(url=self.webapp_url))],
            [InlineKeyboardButton("📧 Поддержка", url="https://t.me/support")],
            [InlineKeyboardButton("💬 Группа", url="https://t.me/flirtly_support")],
            [InlineKeyboardButton("◀️ Назад", callback_data="back_to_start")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            help_text,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )
    
    async def handle_callback(self, update: Update, context):
        """Обработка inline кнопок"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        user_id = query.from_user.id
        
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
            await self.start_chat(user_id, match_id, query)
        
        elif data == "referral":
            await self.show_referral(user_id, query)
        
        elif data == "free_trial":
            await self.activate_free_trial(user_id, query)
    
    async def handle_message(self, update: Update, context):
        """Обработка сообщений в чате"""
        user_id = update.effective_user.id
        message_text = update.message.text
        
        # Проверяем есть ли активный чат
        active_chat = await self.get_active_chat(user_id)
        
        if active_chat:
            # Пересылаем сообщение матчу
            await self.forward_message_to_match(
                from_user=user_id,
                to_user=active_chat['partner_id'],
                message=message_text
            )
            
            await update.message.reply_text("✅ Сообщение отправлено!")
        else:
            # Нет активного чата - направляем в Web App
            await update.message.reply_text(
                "💬 У тебя нет активных чатов.\n\n"
                "Открой Web App чтобы начать общение!",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⚡ Открыть чаты", 
                                       web_app=WebAppInfo(url=f"{self.webapp_url}/chats"))
                ]])
            )
    
    # ===================================
    # HELPER METHODS (Mock implementations)
    # ===================================
    
    async def check_user_exists(self, user_id: int) -> bool:
        """Проверка существования пользователя"""
        # Mock implementation
        return True
    
    async def get_user_data(self, user_id: int) -> dict:
        """Получение данных пользователя"""
        # Mock implementation
        return {
            'name': 'Тестовый пользователь',
            'age': 25,
            'gender': 'male',
            'looking_for': 'female',
            'city': 'Москва',
            'likes_sent': 5,
            'likes_received': 12,
            'matches_count': 3,
            'active_chats': 1,
            'is_premium': False,
            'premium_until': None,
            'photos': ['photo1.jpg', 'photo2.jpg']
        }
    
    async def get_user_matches(self, user_id: int) -> list:
        """Получение матчей пользователя"""
        # Mock implementation
        return [
            {'id': 1, 'name': 'Анна', 'age': 23},
            {'id': 2, 'name': 'Мария', 'age': 26},
            {'id': 3, 'name': 'Елена', 'age': 24}
        ]
    
    async def get_active_chat(self, user_id: int) -> Optional[dict]:
        """Получение активного чата"""
        # Mock implementation
        return None
    
    async def forward_message_to_match(self, from_user: int, to_user: int, message: str):
        """Пересылка сообщения матчу"""
        # Mock implementation
        pass
    
    async def start_chat(self, user_id: int, match_id: int, query):
        """Начало чата с матчем"""
        await query.edit_message_text(
            f"💬 Чат с пользователем {match_id}\n\n"
            "Открой Web App для удобного общения!",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("⚡ Открыть чат", 
                                   web_app=WebAppInfo(url=f"{self.webapp_url}/chat/{match_id}"))
            ]])
        )
    
    async def show_referral(self, user_id: int, query):
        """Показать реферальную программу"""
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
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📤 Поделиться", 
                                   url=f"https://t.me/share/url?url={ref_link}&text=🔥 Попробуй Flirtly!")],
                [InlineKeyboardButton("◀️ Назад", callback_data="back_to_start")]
            ])
        )
    
    async def activate_free_trial(self, user_id: int, query):
        """Активация бесплатного пробного периода"""
        await query.edit_message_text(
            "🎁 <b>Бесплатная неделя Premium активирована!</b>\n\n"
            "Ты получил доступ ко всем Premium функциям на 7 дней:\n"
            "• Безлимитные лайки ❤️\n"
            "• 5 суперлайков в день ⚡\n"
            "• Расширенные фильтры 🔍\n"
            "• Видеть кто лайкнул 👀\n\n"
            "Наслаждайся Premium опытом!",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("⚡ Начать использовать", 
                                   web_app=WebAppInfo(url=self.webapp_url))
            ]])
        )
    
    def run(self):
        """Запуск бота"""
        logger.info("Starting Flirtly Bot...")
        self.app.run_polling()

# Запуск бота
if __name__ == "__main__":
    BOT_TOKEN = os.getenv("BOT_TOKEN", "8430527446:AAFLoCZqvreDpsgz4d5z4J5LXMLC42B9ex0")
    WEBAPP_URL = os.getenv("WEBAPP_URL", "https://vlamay.github.io/flirtly-webapp")
    
    bot = FlirtlyBot(BOT_TOKEN, WEBAPP_URL)
    bot.run()