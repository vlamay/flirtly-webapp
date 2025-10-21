# notification_system.py - Система push-уведомлений

import requests
import json
import sqlite3
import logging
from datetime import datetime, timedelta
import time

logger = logging.getLogger(__name__)

BOT_TOKEN = "8430527446:AAFLoCZqvreDpsgz4d5z4J5LXMLC42B9ex0"
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
DB_PATH = "flirtly.db"

class NotificationSystem:
    def __init__(self):
        self.init_database()
    
    def init_database(self):
        """Инициализация таблицы уведомлений"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                type TEXT NOT NULL,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                data TEXT,
                is_sent BOOLEAN DEFAULT 0,
                sent_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def send_notification(self, user_id, notification_type, title, message, data=None):
        """Отправка уведомления пользователю"""
        try:
            # Получаем telegram_id пользователя
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT telegram_id FROM users WHERE id = ?", (user_id,))
            result = cursor.fetchone()
            
            if not result:
                logger.error(f"User {user_id} not found")
                return False
            
            telegram_id = result[0]
            
            # Создаем клавиатуру в зависимости от типа уведомления
            keyboard = self._create_keyboard(notification_type, data)
            
            # Отправляем сообщение
            url = f"{BASE_URL}/sendMessage"
            payload = {
                "chat_id": telegram_id,
                "text": f"🔔 <b>{title}</b>\n\n{message}",
                "parse_mode": "HTML"
            }
            
            if keyboard:
                payload["reply_markup"] = json.dumps(keyboard)
            
            response = requests.post(url, json=payload)
            
            if response.json().get("ok"):
                # Сохраняем уведомление в БД
                self._save_notification(user_id, notification_type, title, message, data)
                logger.info(f"Notification sent to user {user_id} ({telegram_id})")
                return True
            else:
                logger.error(f"Failed to send notification: {response.json()}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
            return False
        finally:
            conn.close()
    
    def _create_keyboard(self, notification_type, data):
        """Создание клавиатуры для уведомления"""
        keyboards = {
            'match': {
                "inline_keyboard": [
                    [{"text": "💬 Написать", "callback_data": f"chat_{data.get('match_id')}"}],
                    [{"text": "👀 Смотреть профиль", "callback_data": f"view_{data.get('partner_id')}"}]
                ]
            },
            'like': {
                "inline_keyboard": [
                    [{"text": "👀 Посмотреть профиль", "callback_data": f"view_{data.get('liker_id')}"}],
                    [{"text": "⚡ Открыть Flirtly", "web_app": {"url": "https://vlamay.github.io/flirtly-webapp"}}]
                ]
            },
            'message': {
                "inline_keyboard": [
                    [{"text": "💬 Ответить", "callback_data": f"chat_{data.get('match_id')}"}],
                    [{"text": "⚡ Открыть чат", "web_app": {"url": f"https://vlamay.github.io/flirtly-webapp/chat/{data.get('match_id')}"}}]
                ]
            },
            'premium': {
                "inline_keyboard": [
                    [{"text": "⭐ Купить Premium", "callback_data": "buy_premium"}],
                    [{"text": "🎁 Попробовать бесплатно", "callback_data": "free_trial"}]
                ]
            },
            'activity': {
                "inline_keyboard": [
                    [{"text": "⚡ Открыть Flirtly", "web_app": {"url": "https://vlamay.github.io/flirtly-webapp"}}]
                ]
            }
        }
        
        return keyboards.get(notification_type)
    
    def _save_notification(self, user_id, notification_type, title, message, data):
        """Сохранение уведомления в БД"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO notifications (user_id, type, title, message, data, is_sent, sent_at)
            VALUES (?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP)
        ''', (user_id, notification_type, title, message, json.dumps(data) if data else None))
        
        conn.commit()
        conn.close()
    
    def send_match_notification(self, user_id, partner_name, partner_age, match_id):
        """Уведомление о новом матче"""
        title = "🎉 Новый матч!"
        message = f"{partner_name}, {partner_age} тоже лайкнул(а) тебя!\n\nЭто взаимная симпатия! Начните общаться!"
        
        data = {
            'match_id': match_id,
            'partner_name': partner_name,
            'partner_age': partner_age
        }
        
        return self.send_notification(user_id, 'match', title, message, data)
    
    def send_like_notification(self, user_id, liker_name, liker_age, liker_id):
        """Уведомление о лайке"""
        title = "❤️ Кто-то лайкнул твой профиль!"
        message = f"{liker_name}, {liker_age} понравился твой профиль!\n\nЛайкни в ответ и получи матч!"
        
        data = {
            'liker_id': liker_id,
            'liker_name': liker_name,
            'liker_age': liker_age
        }
        
        return self.send_notification(user_id, 'like', title, message, data)
    
    def send_message_notification(self, user_id, sender_name, message_preview, match_id):
        """Уведомление о новом сообщении"""
        title = f"💬 Новое сообщение от {sender_name}"
        message = f"{message_preview[:100]}{'...' if len(message_preview) > 100 else ''}\n\nОтвечай быстро для лучшего общения!"
        
        data = {
            'match_id': match_id,
            'sender_name': sender_name
        }
        
        return self.send_notification(user_id, 'message', title, message, data)
    
    def send_premium_offer_notification(self, user_id):
        """Уведомление о предложении Premium"""
        title = "⭐ Специальное предложение!"
        message = "Первая неделя Premium - БЕСПЛАТНО! 🎁\n\n• Безлимитные лайки ❤️\n• 5 суперлайков в день ⚡\n• Расширенные фильтры 🔍\n• Видеть кто лайкнул 👀\n\nОграниченное время! Активируй сейчас!"
        
        return self.send_notification(user_id, 'premium', title, message)
    
    def send_activity_reminder(self, user_id, days_inactive):
        """Напоминание об активности"""
        if days_inactive == 1:
            title = "💔 Мы скучаем!"
            message = "Ты не заходил в Flirtly целый день.\n\nВозможно, кто-то уже лайкнул твой профиль! Проверь прямо сейчас!"
        elif days_inactive == 3:
            title = "🔥 Не упусти возможности!"
            message = "За 3 дня без тебя в Flirtly произошло много интересного:\n• Новые пользователи в твоем городе\n• Возможные матчи ждут твоего внимания\n• Лайки накапливаются...\n\nВернись и найди свою любовь!"
        elif days_inactive == 7:
            title = "💌 Долго не виделись!"
            message = "Прошла целая неделя без тебя в Flirtly.\n\nЗа это время:\n• +50 новых пользователей в твоем городе\n• 12 потенциальных матчей\n• 5 лайков на твой профиль\n\nНе упускай шанс найти любовь!"
        else:
            return False
        
        return self.send_notification(user_id, 'activity', title, message)
    
    def send_boost_notification(self, user_id):
        """Уведомление о доступном бусте"""
        title = "🚀 Буст профиля доступен!"
        message = "Получи в 10 раз больше просмотров на 30 минут!\n\n• Твой профиль будет показан первым\n• Больше лайков и матчей\n• Приоритет в рекомендациях\n\nИспользуй буст и найди больше матчей!"
        
        return self.send_notification(user_id, 'boost', title, message)
    
    def send_custom_notification(self, user_id, title, message):
        """Отправка кастомного уведомления"""
        return self.send_notification(user_id, 'custom', title, message)
    
    def send_bulk_notification(self, user_ids, title, message, notification_type='custom'):
        """Массовая рассылка уведомлений"""
        success_count = 0
        
        for user_id in user_ids:
            if self.send_notification(user_id, notification_type, title, message):
                success_count += 1
            time.sleep(0.1)  # Задержка между отправками
        
        logger.info(f"Bulk notification sent: {success_count}/{len(user_ids)}")
        return success_count
    
    def get_notification_history(self, user_id, limit=50):
        """Получение истории уведомлений пользователя"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT type, title, message, is_sent, sent_at, created_at
            FROM notifications
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        ''', (user_id, limit))
        
        notifications = cursor.fetchall()
        conn.close()
        
        return notifications
    
    def mark_notification_as_read(self, notification_id):
        """Отметить уведомление как прочитанное"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE notifications
            SET is_read = 1, read_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (notification_id,))
        
        conn.commit()
        conn.close()
    
    def get_unread_notifications_count(self, user_id):
        """Получение количества непрочитанных уведомлений"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT COUNT(*) FROM notifications
            WHERE user_id = ? AND is_sent = 1 AND (is_read = 0 OR is_read IS NULL)
        ''', (user_id,))
        
        count = cursor.fetchone()[0]
        conn.close()
        
        return count
    
    def cleanup_old_notifications(self, days=30):
        """Очистка старых уведомлений"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            DELETE FROM notifications
            WHERE created_at < datetime('now', '-{} days')
        '''.format(days))
        
        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()
        
        logger.info(f"Cleaned up {deleted_count} old notifications")
        return deleted_count

# Scheduler для автоматических уведомлений
class NotificationScheduler:
    def __init__(self):
        self.notification_system = NotificationSystem()
        self.running = False
    
    def start(self):
        """Запуск планировщика"""
        self.running = True
        logger.info("Notification scheduler started")
        
        while self.running:
            try:
                self._send_daily_notifications()
                time.sleep(3600)  # Проверяем каждый час
            except Exception as e:
                logger.error(f"Error in notification scheduler: {e}")
                time.sleep(300)  # Ждем 5 минут при ошибке
    
    def stop(self):
        """Остановка планировщика"""
        self.running = False
        logger.info("Notification scheduler stopped")
    
    def _send_daily_notifications(self):
        """Отправка ежедневных уведомлений"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Неактивные пользователи
        cursor.execute('''
            SELECT id, name, last_active FROM users
            WHERE is_active = 1 AND last_active < datetime('now', '-1 day')
        ''')
        
        inactive_users = cursor.fetchall()
        
        for user_id, name, last_active in inactive_users:
            days_inactive = (datetime.now() - datetime.strptime(last_active, '%Y-%m-%d %H:%M:%S')).days
            self.notification_system.send_activity_reminder(user_id, days_inactive)
        
        # Пользователи без Premium
        cursor.execute('''
            SELECT id FROM users
            WHERE is_active = 1 AND (is_premium = 0 OR premium_until < datetime('now'))
            ORDER BY RANDOM()
            LIMIT 10
        ''')
        
        free_users = [row[0] for row in cursor.fetchall()]
        
        for user_id in free_users:
            self.notification_system.send_premium_offer_notification(user_id)
        
        conn.close()

if __name__ == "__main__":
    # Тестирование системы уведомлений
    notification_system = NotificationSystem()
    
    # Пример отправки уведомления
    notification_system.send_match_notification(1, "Анна", 25, 1)
    notification_system.send_like_notification(1, "Михаил", 28, 2)
    notification_system.send_message_notification(1, "Елена", "Привет! Как дела?", 1)
    
    print("Notification system test completed")
