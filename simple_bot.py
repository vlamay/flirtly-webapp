# simple_bot.py - Простейший бот для тестирования команд

import requests
import json
import time
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = "8430527446:AAFLoCZqvreDpsgz4d5z4J5LXMLC42B9ex0"
WEBAPP_URL = "https://vlamay.github.io/flirtly-webapp"
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

class SimpleBot:
    def __init__(self):
        self.last_update_id = 0
        self.running = True
    
    def send_message(self, chat_id, text, reply_markup=None):
        """Отправка сообщения"""
        url = f"{BASE_URL}/sendMessage"
        data = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML"
        }
        
        if reply_markup:
            data["reply_markup"] = json.dumps(reply_markup)
        
        response = requests.post(url, json=data)
        return response.json()
    
    def get_updates(self):
        """Получение обновлений"""
        url = f"{BASE_URL}/getUpdates"
        params = {
            "offset": self.last_update_id + 1,
            "timeout": 30
        }
        
        response = requests.get(url, params=params)
        return response.json()
    
    def handle_command(self, update):
        """Обработка команд"""
        message = update["message"]
        chat_id = message["chat"]["id"]
        user = message["from"]
        text = message.get("text", "")
        
        logger.info(f"User {user['id']} ({user.get('first_name', 'Unknown')}) sent: {text}")
        
        if text.startswith("/start"):
            self.handle_start(chat_id, user)
        elif text.startswith("/profile"):
            self.handle_profile(chat_id, user)
        elif text.startswith("/matches"):
            self.handle_matches(chat_id, user)
        elif text.startswith("/search"):
            self.handle_search(chat_id, user)
        elif text.startswith("/premium"):
            self.handle_premium(chat_id, user)
        elif text.startswith("/settings"):
            self.handle_settings(chat_id, user)
        elif text.startswith("/help"):
            self.handle_help(chat_id, user)
        else:
            self.handle_message(chat_id, user)
    
    def handle_start(self, chat_id, user):
        """Обработка /start"""
        keyboard = {
            "inline_keyboard": [
                [{"text": "⚡ Открыть Flirtly", "web_app": {"url": WEBAPP_URL}}],
                [
                    {"text": "👤 Мой профиль", "callback_data": "profile"},
                    {"text": "💕 Мои матчи", "callback_data": "matches"}
                ],
                [
                    {"text": "🔍 Искать", "callback_data": "search"},
                    {"text": "💬 Чаты", "callback_data": "chats"}
                ],
                [
                    {"text": "⭐ Premium", "callback_data": "premium"},
                    {"text": "⚙️ Настройки", "callback_data": "settings"}
                ],
                [{"text": "🎁 Пригласить друзей", "callback_data": "referral"}]
            ]
        }
        
        text = f"""🔥 <b>Привет, {user.get('first_name', 'друг')}!</b>

Добро пожаловать в <b>Flirtly</b> ⚡ - знакомства нового уровня!

<b>Что тебя ждет:</b>
• 💕 Умный подбор совпадений
• ⚡ Swipe как в популярных приложениях
• 💬 Общение прямо в Telegram
• 🎁 Бонусы за приглашения друзей

<b>Нажми кнопку ниже чтобы начать!</b>"""
        
        self.send_message(chat_id, text, keyboard)
    
    def handle_profile(self, chat_id, user):
        """Обработка /profile"""
        keyboard = {
            "inline_keyboard": [
                [{"text": "✏️ Редактировать", "web_app": {"url": f"{WEBAPP_URL}/profile"}}],
                [{"text": "📸 Добавить фото", "callback_data": "add_photo"}],
                [{"text": "◀️ Назад", "callback_data": "back_to_start"}]
            ]
        }
        
        text = f"""👤 <b>Твой профиль</b>

<b>Основная информация:</b>
• Имя: {user.get('first_name', 'Не указано')}
• Username: @{user.get('username', 'Не указан')}
• ID: {user['id']}

<b>Статистика:</b>
• ❤️ Лайков отправлено: 5
• 💕 Получено лайков: 12
• 🎯 Совпадений: 3
• 📸 Фото: 2

<b>Подписка:</b>
• Статус: 🆓 Бесплатная"""
        
        self.send_message(chat_id, text, keyboard)
    
    def handle_matches(self, chat_id, user):
        """Обработка /matches"""
        keyboard = {
            "inline_keyboard": [
                [{"text": "💬 Чат с Анной", "callback_data": "chat_1"}],
                [{"text": "💬 Чат с Марией", "callback_data": "chat_2"}],
                [{"text": "💬 Чат с Еленой", "callback_data": "chat_3"}],
                [{"text": "👀 Все совпадения", "web_app": {"url": f"{WEBAPP_URL}/matches"}}],
                [{"text": "◀️ Назад", "callback_data": "back_to_start"}]
            ]
        }
        
        text = """💕 <b>Мои совпадения</b>

1. <b>Анна, 25</b> • Москва
2. <b>Мария, 26</b> • Санкт-Петербург  
3. <b>Елена, 24</b> • Казань

<b>У тебя 3 активных совпадения!</b>"""
        
        self.send_message(chat_id, text, keyboard)
    
    def handle_search(self, chat_id, user):
        """Обработка /search"""
        keyboard = {
            "inline_keyboard": [
                [{"text": "⚡ Начать свайпать", "web_app": {"url": WEBAPP_URL}}],
                [{"text": "⚙️ Настроить фильтры", "callback_data": "filters"}],
                [{"text": "◀️ Назад", "callback_data": "back_to_start"}]
            ]
        }
        
        text = """🔍 <b>Поиск анкет</b>

<b>Готов искать новые знакомства!</b>

<b>Твои настройки:</b>
• Возраст: 18-35
• Пол: Женщины
• Расстояние: 50 км

<b>Лайков осталось: 5</b>

<b>Начни свайпать прямо сейчас!</b>"""
        
        self.send_message(chat_id, text, keyboard)
    
    def handle_premium(self, chat_id, user):
        """Обработка /premium"""
        keyboard = {
            "inline_keyboard": [
                [{"text": "⭐ Купить Premium", "web_app": {"url": f"{WEBAPP_URL}/premium"}}],
                [{"text": "💎 Купить Platinum", "web_app": {"url": f"{WEBAPP_URL}/premium"}}],
                [{"text": "🎁 Попробовать бесплатно", "callback_data": "free_trial"}],
                [{"text": "◀️ Назад", "callback_data": "back_to_start"}]
            ]
        }
        
        text = """⭐ <b>Premium подписка</b>

<b>🌟 PREMIUM (250 ⭐/месяц)</b>
• Безлимитные лайки ❤️
• 5 суперлайков в день ⚡
• Расширенные фильтры 🔍
• Видеть кто лайкнул 👀
• Приоритет в показе 📊

<b>💎 PLATINUM (500 ⭐/месяц)</b>
• Всё из Premium +
• AI совместимость 🤖
• Инкогни-taking режим 👻
• Видеть все просмотры 👁️
• Персональные рекомендации 🎯

<b>💳 Telegram Stars</b>
Оплата через Telegram Stars - быстро и безопасно!

<b>Специальное предложение:</b>
• Первая неделя Premium - БЕСПЛАТНО! 🎁
• При оплате на месяц - скидка 20% 💰"""
        
        self.send_message(chat_id, text, keyboard)
    
    def handle_settings(self, chat_id, user):
        """Обработка /settings"""
        keyboard = {
            "inline_keyboard": [
                [{"text": "🔔 Уведомления", "callback_data": "notifications"}],
                [{"text": "🔒 Приватность", "callback_data": "privacy"}],
                [{"text": "🔍 Фильтры", "callback_data": "filters"}],
                [{"text": "📱 Управление через Web App", "web_app": {"url": f"{WEBAPP_URL}/settings"}}],
                [{"text": "◀️ Назад", "callback_data": "back_to_start"}]
            ]
        }
        
        text = """⚙️ <b>Настройки</b>

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
• Только с фото: ❌"""
        
        self.send_message(chat_id, text, keyboard)
    
    def handle_help(self, chat_id, user):
        """Обработка /help"""
        keyboard = {
            "inline_keyboard": [
                [{"text": "⚡ Открыть Web App", "web_app": {"url": WEBAPP_URL}}],
                [{"text": "📧 Поддержка", "url": "https://t.me/support"}],
                [{"text": "💬 Группа", "url": "https://t.me/flirtly_support"}],
                [{"text": "◀️ Назад", "callback_data": "back_to_start"}]
            ]
        }
        
        text = """ℹ️ <b>Помощь</b>

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
• 🌐 Сайт: https://flirtly.app"""
        
        self.send_message(chat_id, text, keyboard)
    
    def handle_message(self, chat_id, user):
        """Обработка обычных сообщений"""
        keyboard = {
            "inline_keyboard": [
                [{"text": "⚡ Открыть Web App", "web_app": {"url": WEBAPP_URL}}]
            ]
        }
        
        text = """💬 <b>Привет!</b>

Я бот для знакомств Flirtly! Используй команды:

/start - Главное меню
/profile - Мой профиль
/matches - Мои совпадения
/search - Поиск анкет
/premium - Premium подписка
/help - Помощь

Или открой Web App для полного функционала!"""
        
        self.send_message(chat_id, text, keyboard)
    
    def run(self):
        """Запуск бота"""
        logger.info("Starting Simple Bot...")
        
        while self.running:
            try:
                updates = self.get_updates()
                
                if updates.get("ok"):
                    for update in updates["result"]:
                        self.last_update_id = update["update_id"]
                        
                        if "message" in update:
                            self.handle_command(update)
                
                time.sleep(1)
                
            except KeyboardInterrupt:
                logger.info("Bot stopped by user")
                self.running = False
            except Exception as e:
                logger.error(f"Error: {e}")
                time.sleep(5)

if __name__ == "__main__":
    bot = SimpleBot()
    bot.run()
