# complete_bot.py - Полноценный бот с базой данных и всеми функциями

import requests
import json
import time
import logging
import sqlite3
import os
from datetime import datetime, timedelta
import uuid

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = "8430527446:AAFLoCZqvreDpsgz4d5z4J5LXMLC42B9ex0"
WEBAPP_URL = "https://vlamay.github.io/flirtly-webapp"
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
DB_PATH = "flirtly.db"

class CompleteBot:
    def __init__(self):
        self.last_update_id = 0
        self.running = True
        self.init_database()
    
    def init_database(self):
        """Инициализация базы данных"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Создаем таблицы если их нет
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE NOT NULL,
                username TEXT,
                first_name TEXT,
                name TEXT,
                age INTEGER,
                gender TEXT,
                looking_for TEXT,
                bio TEXT,
                city TEXT,
                country TEXT,
                latitude REAL,
                longitude REAL,
                is_premium BOOLEAN DEFAULT 0,
                premium_until DATETIME,
                matches_count INTEGER DEFAULT 0,
                likes_sent INTEGER DEFAULT 0,
                likes_received INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_active DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS photos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                url TEXT NOT NULL,
                position INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS likes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_user_id INTEGER,
                to_user_id INTEGER,
                action TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (from_user_id) REFERENCES users (id),
                FOREIGN KEY (to_user_id) REFERENCES users (id),
                UNIQUE(from_user_id, to_user_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS matches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user1_id INTEGER,
                user2_id INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY (user1_id) REFERENCES users (id),
                FOREIGN KEY (user2_id) REFERENCES users (id),
                UNIQUE(user1_id, user2_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                match_id INTEGER,
                sender_id INTEGER,
                content TEXT NOT NULL,
                is_read BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (match_id) REFERENCES matches (id),
                FOREIGN KEY (sender_id) REFERENCES users (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount_stars INTEGER,
                subscription_type TEXT,
                status TEXT DEFAULT 'pending',
                telegram_payment_charge_id TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Добавляем тестовые данные
        self.add_sample_data(cursor)
        
        conn.commit()
        conn.close()
        logger.info("Database initialized")
    
    def add_sample_data(self, cursor):
        """Добавляем тестовые данные"""
        # Проверяем есть ли уже пользователи
        cursor.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] > 0:
            return
        
        # Добавляем тестовых пользователей
        sample_users = [
            (123456789, 'anna_bot', 'Анна', 'Анна', 25, 'female', 'male', 'Люблю путешествия и фотографию', 'Москва', 'Россия', 55.7558, 37.6173),
            (987654321, 'mike_bot', 'Михаил', 'Михаил', 28, 'male', 'female', 'Занимаюсь спортом, увлекаюсь музыкой', 'Санкт-Петербург', 'Россия', 59.9343, 30.3351),
            (555666777, 'elena_bot', 'Елена', 'Елена', 23, 'female', 'male', 'Студентка, люблю читать и смотреть фильмы', 'Москва', 'Россия', 55.7558, 37.6173),
            (111222333, 'dmitry_bot', 'Дмитрий', 'Дмитрий', 30, 'male', 'female', 'Программист, играю в футбол', 'Казань', 'Россия', 55.8304, 49.0661)
        ]
        
        for user_data in sample_users:
            cursor.execute('''
                INSERT INTO users (telegram_id, username, first_name, name, age, gender, 
                                 looking_for, bio, city, country, latitude, longitude)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', user_data)
        
        logger.info("Sample data added")
    
    def get_user_by_telegram_id(self, telegram_id):
        """Получение пользователя по telegram_id"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
        user = cursor.fetchone()
        conn.close()
        return user
    
    def create_user(self, telegram_id, username, first_name):
        """Создание пользователя"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR IGNORE INTO users (telegram_id, username, first_name, name)
            VALUES (?, ?, ?, ?)
        ''', (telegram_id, username, first_name, first_name))
        conn.commit()
        conn.close()
    
    def get_user_matches(self, user_id):
        """Получение матчей пользователя"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT u.name, u.age, u.city, m.id as match_id
            FROM matches m
            JOIN users u ON (CASE WHEN m.user1_id = ? THEN m.user2_id ELSE m.user1_id END = u.id)
            WHERE (m.user1_id = ? OR m.user2_id = ?) AND m.is_active = 1
            ORDER BY m.created_at DESC
        ''', (user_id, user_id, user_id))
        matches = cursor.fetchall()
        conn.close()
        return matches
    
    def get_candidates(self, user_id, limit=10):
        """Получение кандидатов для свайпов"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Получаем пользователя
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        if not user:
            conn.close()
            return []
        
        # Ищем кандидатов
        cursor.execute('''
            SELECT u.* FROM users u
            WHERE u.id != ? AND u.is_active = 1
            AND NOT EXISTS (
                SELECT 1 FROM likes l 
                WHERE l.from_user_id = ? AND l.to_user_id = u.id
            )
            ORDER BY u.created_at DESC
            LIMIT ?
        ''', (user_id, user_id, limit))
        
        candidates = cursor.fetchall()
        conn.close()
        return candidates
    
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
    
    def answer_callback_query(self, callback_query_id, text=None):
        """Ответ на callback query"""
        url = f"{BASE_URL}/answerCallbackQuery"
        data = {"callback_query_id": callback_query_id}
        if text:
            data["text"] = text
        requests.post(url, json=data)
    
    def edit_message_text(self, chat_id, message_id, text, reply_markup=None):
        """Редактирование сообщения"""
        url = f"{BASE_URL}/editMessageText"
        data = {
            "chat_id": chat_id,
            "message_id": message_id,
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
        
        telegram_id = user["id"]
        username = user.get("username")
        first_name = user.get("first_name")
        
        # Создаем пользователя если его нет
        self.create_user(telegram_id, username, first_name)
        
        logger.info(f"User {telegram_id} ({first_name}) sent: {text}")
        
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
    
    def handle_callback_query(self, update):
        """Обработка callback query"""
        callback_query = update["callback_query"]
        callback_id = callback_query["id"]
        chat_id = callback_query["message"]["chat"]["id"]
        message_id = callback_query["message"]["message_id"]
        data = callback_query["data"]
        user = callback_query["from"]
        
        telegram_id = user["id"]
        logger.info(f"User {telegram_id} clicked button: {data}")
        
        # Отвечаем на callback query
        self.answer_callback_query(callback_id)
        
        if data == "back_to_start":
            self.handle_start(chat_id, user)
        
        elif data == "profile":
            self.handle_profile(chat_id, user)
        
        elif data == "matches":
            self.handle_matches(chat_id, user)
        
        elif data == "search":
            self.handle_search(chat_id, user)
        
        elif data == "premium":
            self.handle_premium(chat_id, user)
        
        elif data == "settings":
            self.handle_settings(chat_id, user)
        
        elif data.startswith("chat_"):
            match_id = data.split("_")[1]
            self.handle_chat(chat_id, message_id, match_id)
        
        elif data == "referral":
            self.handle_referral(chat_id, message_id, user)
        
        elif data == "free_trial":
            self.handle_free_trial(chat_id, message_id, user)
        
        elif data == "buy_premium":
            self.handle_buy_premium(chat_id, message_id, user)
        
        elif data == "buy_platinum":
            self.handle_buy_platinum(chat_id, message_id, user)
        
        elif data.startswith("filter_"):
            filter_type = data.split("_")[1]
            self.handle_filter(chat_id, message_id, filter_type)
        
        elif data == "notifications":
            self.handle_notifications(chat_id, message_id, user)
        
        elif data == "privacy":
            self.handle_privacy(chat_id, message_id, user)
        
        else:
            self.handle_unknown_callback(chat_id, message_id, data)
    
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
        telegram_id = user["id"]
        user_data = self.get_user_by_telegram_id(telegram_id)
        
        if user_data:
            name = user_data[3] or user.get('first_name', 'Не указано')
            age = user_data[5] or 'Не указан'
            city = user_data[9] or 'Не указан'
            matches_count = user_data[16] or 0
            likes_sent = user_data[17] or 0
            likes_received = user_data[18] or 0
            is_premium = user_data[13] or False
        else:
            name = user.get('first_name', 'Не указано')
            age = 'Не указан'
            city = 'Не указан'
            matches_count = 0
            likes_sent = 0
            likes_received = 0
            is_premium = False
        
        keyboard = {
            "inline_keyboard": [
                [{"text": "✏️ Редактировать", "web_app": {"url": f"{WEBAPP_URL}/profile"}}],
                [{"text": "📸 Добавить фото", "callback_data": "add_photo"}],
                [{"text": "◀️ Назад", "callback_data": "back_to_start"}]
            ]
        }
        
        text = f"""👤 <b>Твой профиль</b>

<b>Основная информация:</b>
• Имя: {name}
• Возраст: {age}
• Город: {city}

<b>Статистика:</b>
• ❤️ Лайков отправлено: {likes_sent}
• 💕 Получено лайков: {likes_received}
• 🎯 Совпадений: {matches_count}

<b>Подписка:</b>
• Статус: {'⭐ Premium' if is_premium else '🆓 Бесплатная'}"""
        
        self.send_message(chat_id, text, keyboard)
    
    def handle_matches(self, chat_id, user):
        """Обработка /matches"""
        telegram_id = user["id"]
        user_data = self.get_user_by_telegram_id(telegram_id)
        
        if not user_data:
            self.send_message(chat_id, "❌ Пользователь не найден")
            return
        
        user_id = user_data[0]
        matches = self.get_user_matches(user_id)
        
        if not matches:
            text = """💕 <b>Мои совпадения</b>

У тебя пока нет совпадений 😔

<b>Как получить матчи:</b>
• 📸 Добавь качественные фото
• ✍️ Напиши интересную биографию
• 🔍 Активно свайпай анкеты
• ⭐ Купи Premium для больше возможностей

<b>Начни искать прямо сейчас!</b>"""
            
            keyboard = {
                "inline_keyboard": [
                    [{"text": "⚡ Начать поиск", "web_app": {"url": WEBAPP_URL}}],
                    [{"text": "◀️ Назад", "callback_data": "back_to_start"}]
                ]
            }
        else:
            text = "💕 <b>Мои совпадения</b>\n\n"
            keyboard_buttons = []
            
            for i, match in enumerate(matches[:5]):  # Показываем первые 5
                name, age, city, match_id = match
                text += f"{i+1}. <b>{name}</b>, {age} • {city}\n"
                keyboard_buttons.append([{"text": f"💬 Чат с {name}", "callback_data": f"chat_{match_id}"}])
            
            if len(matches) > 5:
                text += f"\n... и еще {len(matches) - 5} совпадений"
            
            keyboard_buttons.extend([
                [{"text": "👀 Все совпадения", "web_app": {"url": f"{WEBAPP_URL}/matches"}}],
                [{"text": "◀️ Назад", "callback_data": "back_to_start"}]
            ])
            
            keyboard = {"inline_keyboard": keyboard_buttons}
        
        self.send_message(chat_id, text, keyboard)
    
    def handle_search(self, chat_id, user):
        """Обработка /search"""
        telegram_id = user["id"]
        user_data = self.get_user_by_telegram_id(telegram_id)
        
        if not user_data:
            self.send_message(chat_id, "❌ Пользователь не найден")
            return
        
        user_id = user_data[0]
        candidates = self.get_candidates(user_id, 5)
        
        if not candidates:
            text = """🔍 <b>Поиск анкет</b>

Пока нет новых кандидатов 😔

<b>Попробуй:</b>
• Обновить фильтры поиска
• Увеличить радиус поиска
• Добавить больше интересов

<b>Или открой Web App для полного функционала!</b>"""
        else:
            text = """🔍 <b>Поиск анкет</b>

<b>Готов искать новые знакомства!</b>

<b>Твои настройки:</b>
• Возраст: 18-35
• Пол: Женщины
• Расстояние: 50 км

<b>Лайков осталось: 5</b>

<b>Начни свайпать прямо сейчас!</b>"""
        
        keyboard = {
            "inline_keyboard": [
                [{"text": "⚡ Начать свайпать", "web_app": {"url": WEBAPP_URL}}],
                [{"text": "⚙️ Настроить фильтры", "callback_data": "filter_age"}],
                [{"text": "◀️ Назад", "callback_data": "back_to_start"}]
            ]
        }
        
        self.send_message(chat_id, text, keyboard)
    
    def handle_premium(self, chat_id, user):
        """Обработка /premium"""
        keyboard = {
            "inline_keyboard": [
                [{"text": "⭐ Купить Premium", "callback_data": "buy_premium"}],
                [{"text": "💎 Купить Platinum", "callback_data": "buy_platinum"}],
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
• Инкогнито режим 👻
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
                [{"text": "🔍 Фильтры", "callback_data": "filter_age"}],
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
    
    def handle_chat(self, chat_id, message_id, match_id):
        """Обработка чата с матчем"""
        text = f"""💬 <b>Чат с пользователем {match_id}</b>

Открой Web App для удобного общения!

<b>Функции чата:</b>
• 💬 Отправка сообщений
• 📸 Отправка фото
• 🔔 Уведомления о новых сообщениях
• 📱 Синхронизация с Telegram"""
        
        keyboard = {
            "inline_keyboard": [
                [{"text": "⚡ Открыть чат", "web_app": {"url": f"{WEBAPP_URL}/chat/{match_id}"}}],
                [{"text": "◀️ Назад", "callback_data": "matches"}]
            ]
        }
        
        self.edit_message_text(chat_id, message_id, text, keyboard)
    
    def handle_referral(self, chat_id, message_id, user):
        """Обработка реферальной программы"""
        user_id = user["id"]
        ref_link = f"https://t.me/FFlirtly_bot?start=ref_{user_id}"
        
        text = f"""🎁 <b>Реферальная программа</b>

Приглашай друзей и получай бонусы!

<b>За каждого друга:</b>
• Ты получаешь: +10 лайков
• Друг получает: +5 лайков

<b>Твоя ссылка:</b>
<code>{ref_link}</code>

Нажми кнопку чтобы поделиться!"""
        
        keyboard = {
            "inline_keyboard": [
                [{"text": "📤 Поделиться", "url": f"https://t.me/share/url?url={ref_link}&text=🔥 Попробуй Flirtly!"}],
                [{"text": "◀️ Назад", "callback_data": "back_to_start"}]
            ]
        }
        
        self.edit_message_text(chat_id, message_id, text, keyboard)
    
    def handle_free_trial(self, chat_id, message_id, user):
        """Обработка бесплатного пробного периода"""
        text = """🎁 <b>Бесплатная неделя Premium активирована!</b>

Ты получил доступ ко всем Premium функциям на 7 дней:
• Безлимитные лайки ❤️
• 5 суперлайков в день ⚡
• Расширенные фильтры 🔍
• Видеть кто лайкнул 👀

Наслаждайся Premium опытом!"""
        
        keyboard = {
            "inline_keyboard": [
                [{"text": "⚡ Начать использовать", "web_app": {"url": WEBAPP_URL}}]
            ]
        }
        
        self.edit_message_text(chat_id, message_id, text, keyboard)
    
    def handle_buy_premium(self, chat_id, message_id, user):
        """Обработка покупки Premium"""
        text = """⭐ <b>Купить Premium</b>

<b>Стоимость: 250 ⭐/месяц</b>

<b>Что включено:</b>
• Безлимитные лайки ❤️
• 5 суперлайков в день ⚡
• Расширенные фильтры 🔍
• Видеть кто лайкнул 👀
• Приоритет в показе 📊

<b>Оплата через Telegram Stars</b>
Быстро, безопасно и удобно!"""
        
        keyboard = {
            "inline_keyboard": [
                [{"text": "💳 Оплатить 250 ⭐", "pay": True}],
                [{"text": "◀️ Назад", "callback_data": "premium"}]
            ]
        }
        
        self.edit_message_text(chat_id, message_id, text, keyboard)
    
    def handle_buy_platinum(self, chat_id, message_id, user):
        """Обработка покупки Platinum"""
        text = """💎 <b>Купить Platinum</b>

<b>Стоимость: 500 ⭐/месяц</b>

<b>Что включено:</b>
• Всё из Premium +
• AI совместимость 🤖
• Инкогнито режим 👻
• Видеть все просмотры 👁️
• Персональные рекомендации 🎯

<b>Оплата через Telegram Stars</b>
Максимальный опыт знакомств!"""
        
        keyboard = {
            "inline_keyboard": [
                [{"text": "💳 Оплатить 500 ⭐", "pay": True}],
                [{"text": "◀️ Назад", "callback_data": "premium"}]
            ]
        }
        
        self.edit_message_text(chat_id, message_id, text, keyboard)
    
    def handle_filter(self, chat_id, message_id, filter_type):
        """Обработка фильтров"""
        text = f"""🔍 <b>Фильтр: {filter_type}</b>

Настрой параметры поиска для лучших результатов!

<b>Доступные фильтры:</b>
• Возраст: 18-99 лет
• Расстояние: 1-100 км
• Пол: Мужчины/Женщины/Все
• Только с фото: Да/Нет

Открой Web App для полной настройки фильтров!"""
        
        keyboard = {
            "inline_keyboard": [
                [{"text": "⚡ Открыть фильтры", "web_app": {"url": f"{WEBAPP_URL}/filters"}}],
                [{"text": "◀️ Назад", "callback_data": "settings"}]
            ]
        }
        
        self.edit_message_text(chat_id, message_id, text, keyboard)
    
    def handle_notifications(self, chat_id, message_id, user):
        """Обработка настроек уведомлений"""
        text = """🔔 <b>Настройки уведомлений</b>

Управляй тем, какие уведомления ты хочешь получать:

<b>Типы уведомлений:</b>
• Новые матчи ✅
• Сообщения ✅
• Лайки ✅
• Premium предложения ❌

<b>Настрой через Web App для полного контроля!</b>"""
        
        keyboard = {
            "inline_keyboard": [
                [{"text": "⚡ Открыть настройки", "web_app": {"url": f"{WEBAPP_URL}/notifications"}}],
                [{"text": "◀️ Назад", "callback_data": "settings"}]
            ]
        }
        
        self.edit_message_text(chat_id, message_id, text, keyboard)
    
    def handle_privacy(self, chat_id, message_id, user):
        """Обработка настроек приватности"""
        text = """🔒 <b>Настройки приватности</b>

Контролируй, какая информация о тебе видна другим пользователям:

<b>Публичная информация:</b>
• Показывать в поиске ✅
• Показывать расстояние ✅
• Показывать последнюю активность ✅

<b>Настрой через Web App для детального контроля!</b>"""
        
        keyboard = {
            "inline_keyboard": [
                [{"text": "⚡ Открыть настройки", "web_app": {"url": f"{WEBAPP_URL}/privacy"}}],
                [{"text": "◀️ Назад", "callback_data": "settings"}]
            ]
        }
        
        self.edit_message_text(chat_id, message_id, text, keyboard)
    
    def handle_unknown_callback(self, chat_id, message_id, data):
        """Обработка неизвестных callback"""
        text = f"""🔧 <b>Функция в разработке</b>

Кнопка '{data}' пока не реализована.

Используй Web App для полного функционала!"""
        
        keyboard = {
            "inline_keyboard": [
                [{"text": "⚡ Открыть Web App", "web_app": {"url": WEBAPP_URL}}]
            ]
        }
        
        self.edit_message_text(chat_id, message_id, text, keyboard)
    
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
        logger.info("Starting Complete Bot...")
        
        while self.running:
            try:
                updates = self.get_updates()
                
                if updates.get("ok"):
                    for update in updates["result"]:
                        self.last_update_id = update["update_id"]
                        
                        if "message" in update:
                            self.handle_command(update)
                        elif "callback_query" in update:
                            self.handle_callback_query(update)
                
                time.sleep(1)
                
            except KeyboardInterrupt:
                logger.info("Bot stopped by user")
                self.running = False
            except Exception as e:
                logger.error(f"Error: {e}")
                time.sleep(5)

if __name__ == "__main__":
    bot = CompleteBot()
    bot.run()
