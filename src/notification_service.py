# notification_service.py - Система уведомлений через Telegram Bot

import asyncio
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

logger = logging.getLogger(__name__)

class NotificationService:
    def __init__(self, bot, db_connection, cache_service=None):
        self.bot = bot
        self.db = db_connection
        self.cache = cache_service
        self.webapp_url = "https://vlamay.github.io/flirtly-webapp"
    
    async def send_match_notification(self, user_id: int, match_user_id: int):
        """Уведомление о новом матче"""
        
        try:
            # Получаем информацию о матче
            match_info = await self._get_match_info(user_id, match_user_id)
            if not match_info:
                logger.error(f"Match info not found for users {user_id} and {match_user_id}")
                return
            
            partner = match_info['partner']
            match_id = match_info['match_id']
            
            # Проверяем настройки уведомлений
            if not await self._is_notification_enabled(user_id, 'matches'):
                logger.info(f"Match notifications disabled for user {user_id}")
                return
            
            # Создаем клавиатуру
            keyboard = [
                [InlineKeyboardButton("💬 Написать", callback_data=f"chat_{match_id}")],
                [InlineKeyboardButton("👀 Смотреть профиль", callback_data=f"view_{match_user_id}")],
                [InlineKeyboardButton("⚡ Открыть в Web App", 
                                   web_app=WebAppInfo(url=f"{self.webapp_url}/chat/{match_id}"))]
            ]
            
            # Отправляем уведомление
            message_text = f"""
🎉 <b>Новый матч!</b>

<b>{partner['name']}, {partner['age']}</b> тоже лайкнул(а) тебя!

{b'⭐' if partner['is_premium'] else ''} {partner['city']} • {partner['bio'][:100] if partner['bio'] else 'Нет описания'}...

<b>Это взаимная симпатия! Начните общаться!</b>
            """.strip()
            
            await self.bot.send_message(
                chat_id=user_id,
                text=message_text,
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            
            logger.info(f"Match notification sent to user {user_id}")
            
        except Exception as e:
            logger.error(f"Error sending match notification to {user_id}: {e}")
    
    async def send_like_notification(self, user_id: int, liker_id: int):
        """Уведомление о лайке"""
        
        try:
            # Получаем информацию о лайкнувшем
            liker_info = await self._get_user_info(liker_id)
            if not liker_info:
                logger.error(f"Liker info not found for user {liker_id}")
                return
            
            # Проверяем настройки уведомлений
            if not await self._is_notification_enabled(user_id, 'likes'):
                logger.info(f"Like notifications disabled for user {user_id}")
                return
            
            # Проверяем не спамит ли пользователь
            if await self._is_spam_notification(user_id, 'like', liker_id):
                logger.info(f"Spam prevention: skipping like notification from {liker_id} to {user_id}")
                return
            
            # Создаем клавиатуру
            keyboard = [
                [InlineKeyboardButton("👀 Посмотреть профиль", 
                                   web_app=WebAppInfo(url=f"{self.webapp_url}/profile/{liker_id}"))],
                [InlineKeyboardButton("⚡ Открыть Flirtly", 
                                   web_app=WebAppInfo(url=self.webapp_url))]
            ]
            
            # Отправляем уведомление
            message_text = f"""
❤️ <b>Кто-то лайкнул твой профиль!</b>

<b>{liker_info['name']}, {liker_info['age']}</b> из {liker_info['city']} понравился твой профиль!

{b'⭐' if liker_info['is_premium'] else ''} {liker_info['bio'][:100] if liker_info['bio'] else 'Нет описания'}...

<b>Лайкни в ответ и получи матч! 💕</b>
            """.strip()
            
            await self.bot.send_message(
                chat_id=user_id,
                text=message_text,
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            
            # Сохраняем в кэш для предотвращения спама
            await self._mark_notification_sent(user_id, 'like', liker_id)
            
            logger.info(f"Like notification sent to user {user_id}")
            
        except Exception as e:
            logger.error(f"Error sending like notification to {user_id}: {e}")
    
    async def send_message_notification(self, user_id: int, sender_id: int, 
                                      message_preview: str, match_id: int):
        """Уведомление о новом сообщении"""
        
        try:
            # Получаем информацию об отправителе
            sender_info = await self._get_user_info(sender_id)
            if not sender_info:
                logger.error(f"Sender info not found for user {sender_id}")
                return
            
            # Проверяем настройки уведомлений
            if not await self._is_notification_enabled(user_id, 'messages'):
                logger.info(f"Message notifications disabled for user {user_id}")
                return
            
            # Проверяем не спамит ли пользователь
            if await self._is_spam_notification(user_id, 'message', sender_id):
                logger.info(f"Spam prevention: skipping message notification from {sender_id} to {user_id}")
                return
            
            # Создаем клавиатуру
            keyboard = [
                [InlineKeyboardButton("💬 Ответить в Web App", 
                                   web_app=WebAppInfo(url=f"{self.webapp_url}/chat/{match_id}"))],
                [InlineKeyboardButton("✍️ Ответить здесь", callback_data=f"reply_{match_id}")]
            ]
            
            # Отправляем уведомление
            message_text = f"""
💬 <b>Новое сообщение от {sender_info['name']}, {sender_info['age']}</b>

{message_preview[:100]}{'...' if len(message_preview) > 100 else ''}

<b>Отвечай быстро для лучшего общения! ⚡</b>
            """.strip()
            
            await self.bot.send_message(
                chat_id=user_id,
                text=message_text,
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            
            # Сохраняем в кэш для предотвращения спама
            await self._mark_notification_sent(user_id, 'message', sender_id)
            
            logger.info(f"Message notification sent to user {user_id}")
            
        except Exception as e:
            logger.error(f"Error sending message notification to {user_id}: {e}")
    
    async def send_premium_offer_notification(self, user_id: int, offer_type: str = 'weekly'):
        """Уведомление о Premium предложении"""
        
        try:
            # Проверяем настройки уведомлений
            if not await self._is_notification_enabled(user_id, 'premium'):
                logger.info(f"Premium notifications disabled for user {user_id}")
                return
            
            # Проверяем не показывали ли уже недавно
            if await self._is_recent_notification(user_id, 'premium_offer'):
                logger.info(f"Recent premium offer notification for user {user_id}")
                return
            
            if offer_type == 'weekly':
                message_text = """
⭐ <b>Специальное предложение!</b>

<b>Первая неделя Premium - БЕСПЛАТНО! 🎁</b>

• Безлимитные лайки ❤️
• 5 суперлайков в день ⚡
• Расширенные фильтры 🔍
• Видеть кто лайкнул 👀
• Приоритет в показе 📊

<b>Ограниченное время! Активируй сейчас!</b>
                """
            else:
                message_text = """
⭐ <b>Premium подписка</b>

<b>Получи больше матчей с Premium!</b>

• Безлимитные лайки ❤️
• 5 суперлайков в день ⚡
• Расширенные фильтры 🔍
• Видеть кто лайкнул 👀

<b>Попробуй бесплатно!</b>
                """
            
            keyboard = [
                [InlineKeyboardButton("⭐ Попробовать бесплатно", callback_data="free_trial")],
                [InlineKeyboardButton("💎 Купить Premium", 
                                   web_app=WebAppInfo(url=f"{self.webapp_url}/premium"))],
                [InlineKeyboardButton("❌ Не показывать", callback_data="disable_premium_notifications")]
            ]
            
            await self.bot.send_message(
                chat_id=user_id,
                text=message_text,
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            
            # Сохраняем в кэш
            await self._mark_notification_sent(user_id, 'premium_offer', 'system')
            
            logger.info(f"Premium offer notification sent to user {user_id}")
            
        except Exception as e:
            logger.error(f"Error sending premium offer notification to {user_id}: {e}")
    
    async def send_activity_reminder(self, user_id: int):
        """Напоминание о активности"""
        
        try:
            # Проверяем когда пользователь был активен последний раз
            last_active = await self._get_user_last_active(user_id)
            if not last_active:
                return
            
            days_inactive = (datetime.now() - last_active).days
            
            # Разные сообщения в зависимости от времени неактивности
            if days_inactive == 1:
                message_text = """
💔 <b>Мы скучаем!</b>

Ты не заходил в Flirtly целый день. 

Возможно, кто-то уже лайкнул твой профиль! Проверь прямо сейчас! ⚡
                """
            elif days_inactive == 3:
                message_text = """
🔥 <b>Не упусти возможности!</b>

За 3 дня без тебя в Flirtly произошло много интересного:
• Новые пользователи в твоем городе
• Возможные матчи ждут твоего внимания
• Лайки накапливаются...

<b>Вернись и найди свою любовь! 💕</b>
                """
            elif days_inactive == 7:
                message_text = """
💌 <b>Долго не виделись!</b>

Прошла целая неделя без тебя в Flirtly.

За это время:
• +{new_users} новых пользователей в твоем городе
• {potential_matches} потенциальных матчей
• {likes_count} лайков на твой профиль

<b>Не упускай шанс найти любовь! ❤️</b>
                """
            else:
                return  # Не отправляем для других периодов
            
            keyboard = [
                [InlineKeyboardButton("⚡ Открыть Flirtly", 
                                   web_app=WebAppInfo(url=self.webapp_url))],
                [InlineKeyboardButton("👀 Проверить лайки", 
                                   web_app=WebAppInfo(url=f"{self.webapp_url}/likes"))]
            ]
            
            await self.bot.send_message(
                chat_id=user_id,
                text=message_text,
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            
            logger.info(f"Activity reminder sent to user {user_id} (inactive {days_inactive} days)")
            
        except Exception as e:
            logger.error(f"Error sending activity reminder to {user_id}: {e}")
    
    async def send_boost_notification(self, user_id: int):
        """Уведомление о доступном бусте"""
        
        try:
            # Проверяем есть ли у пользователя буст
            has_boost = await self._has_active_boost(user_id)
            if has_boost:
                return
            
            message_text = """
🚀 <b>Буст профиля доступен!</b>

<b>Получи в 10 раз больше просмотров на 30 минут!</b>

• Твой профиль будет показан первым
• Больше лайков и матчей
• Приоритет в рекомендациях

<b>Используй буст и найди больше матчей! 💕</b>
            """
            
            keyboard = [
                [InlineKeyboardButton("🚀 Активировать буст", callback_data="activate_boost")],
                [InlineKeyboardButton("⚡ Открыть Flirtly", 
                                   web_app=WebAppInfo(url=self.webapp_url))]
            ]
            
            await self.bot.send_message(
                chat_id=user_id,
                text=message_text,
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            
            logger.info(f"Boost notification sent to user {user_id}")
            
        except Exception as e:
            logger.error(f"Error sending boost notification to {user_id}: {e}")
    
    # ===================================
    # PRIVATE METHODS
    # ===================================
    
    async def _get_match_info(self, user_id: int, match_user_id: int) -> Optional[Dict]:
        """Получение информации о матче"""
        
        query = """
            SELECT 
                m.id as match_id,
                u.id, u.name, u.age, u.city, u.bio, u.is_premium
            FROM matches m
            JOIN users u ON (
                CASE 
                    WHEN m.user1_id = $1 THEN m.user2_id
                    ELSE m.user1_id
                END = u.id
            )
            WHERE (m.user1_id = $1 AND m.user2_id = $2) OR (m.user1_id = $2 AND m.user2_id = $1)
        """
        
        try:
            row = await self.db.fetchrow(query, user_id, match_user_id)
            if row:
                return {
                    'match_id': row['match_id'],
                    'partner': {
                        'id': row['id'],
                        'name': row['name'],
                        'age': row['age'],
                        'city': row['city'],
                        'bio': row['bio'],
                        'is_premium': row['is_premium']
                    }
                }
            return None
        except Exception as e:
            logger.error(f"Error getting match info: {e}")
            return None
    
    async def _get_user_info(self, user_id: int) -> Optional[Dict]:
        """Получение информации о пользователе"""
        
        query = """
            SELECT id, name, age, city, bio, is_premium
            FROM users
            WHERE id = $1 AND is_active = true
        """
        
        try:
            row = await self.db.fetchrow(query, user_id)
            if row:
                return {
                    'id': row['id'],
                    'name': row['name'],
                    'age': row['age'],
                    'city': row['city'],
                    'bio': row['bio'],
                    'is_premium': row['is_premium']
                }
            return None
        except Exception as e:
            logger.error(f"Error getting user info: {e}")
            return None
    
    async def _is_notification_enabled(self, user_id: int, notification_type: str) -> bool:
        """Проверка включены ли уведомления"""
        
        if self.cache:
            setting = await self.cache.get(f"notification_settings:{user_id}:{notification_type}")
            if setting is not None:
                return setting == 'true'
        
        # Проверяем в базе данных
        query = """
            SELECT notification_settings
            FROM users
            WHERE id = $1
        """
        
        try:
            row = await self.db.fetchrow(query, user_id)
            if row and row['notification_settings']:
                settings = row['notification_settings']
                return settings.get(notification_type, True)  # По умолчанию включено
            return True
        except Exception as e:
            logger.error(f"Error checking notification settings: {e}")
            return True
    
    async def _is_spam_notification(self, user_id: int, notification_type: str, sender_id: str) -> bool:
        """Проверка на спам уведомлений"""
        
        if self.cache:
            key = f"notification_sent:{user_id}:{notification_type}:{sender_id}"
            return await self.cache.exists(key)
        
        return False
    
    async def _mark_notification_sent(self, user_id: int, notification_type: str, sender_id: str):
        """Отметить уведомление как отправленное"""
        
        if self.cache:
            key = f"notification_sent:{user_id}:{notification_type}:{sender_id}"
            await self.cache.set(key, '1', ttl=3600)  # 1 час
    
    async def _is_recent_notification(self, user_id: int, notification_type: str) -> bool:
        """Проверка недавнего уведомления"""
        
        if self.cache:
            key = f"recent_notification:{user_id}:{notification_type}"
            return await self.cache.exists(key)
        
        return False
    
    async def _get_user_last_active(self, user_id: int) -> Optional[datetime]:
        """Получение времени последней активности"""
        
        query = """
            SELECT last_active
            FROM users
            WHERE id = $1
        """
        
        try:
            row = await self.db.fetchrow(query, user_id)
            return row['last_active'] if row else None
        except Exception as e:
            logger.error(f"Error getting user last active: {e}")
            return None
    
    async def _has_active_boost(self, user_id: int) -> bool:
        """Проверка активного буста"""
        
        # Проверяем в кэше
        if self.cache:
            return await self.cache.exists(f"boost_active:{user_id}")
        
        # Проверяем в базе данных
        query = """
            SELECT COUNT(*) as count
            FROM user_boosts
            WHERE user_id = $1 AND expires_at > NOW()
        """
        
        try:
            row = await self.db.fetchrow(query, user_id)
            return row['count'] > 0 if row else False
        except Exception as e:
            logger.error(f"Error checking active boost: {e}")
            return False

# Scheduler для автоматических уведомлений
class NotificationScheduler:
    def __init__(self, notification_service):
        self.notification_service = notification_service
        self.running = False
    
    async def start(self):
        """Запуск планировщика уведомлений"""
        self.running = True
        logger.info("Notification scheduler started")
        
        # Запускаем задачи
        tasks = [
            self._daily_activity_reminders(),
            self._weekly_premium_offers(),
            self._boost_availability_checks()
        ]
        
        await asyncio.gather(*tasks)
    
    async def stop(self):
        """Остановка планировщика"""
        self.running = False
        logger.info("Notification scheduler stopped")
    
    async def _daily_activity_reminders(self):
        """Ежедневные напоминания об активности"""
        while self.running:
            try:
                # Получаем пользователей неактивных более 1 дня
                inactive_users = await self._get_inactive_users(days=1)
                
                for user_id in inactive_users:
                    await self.notification_service.send_activity_reminder(user_id)
                    await asyncio.sleep(1)  # Не спамим
                
                # Ждем до следующего дня
                await asyncio.sleep(24 * 3600)  # 24 часа
                
            except Exception as e:
                logger.error(f"Error in daily activity reminders: {e}")
                await asyncio.sleep(3600)  # Ждем час при ошибке
    
    async def _weekly_premium_offers(self):
        """Еженедельные предложения Premium"""
        while self.running:
            try:
                # Получаем пользователей без Premium
                free_users = await self._get_free_users()
                
                for user_id in free_users:
                    await self.notification_service.send_premium_offer_notification(user_id, 'weekly')
                    await asyncio.sleep(2)  # Не спамим
                
                # Ждем неделю
                await asyncio.sleep(7 * 24 * 3600)  # 7 дней
                
            except Exception as e:
                logger.error(f"Error in weekly premium offers: {e}")
                await asyncio.sleep(3600)  # Ждем час при ошибке
    
    async def _boost_availability_checks(self):
        """Проверки доступности бустов"""
        while self.running:
            try:
                # Получаем активных пользователей без буста
                active_users = await self._get_active_users_without_boost()
                
                for user_id in active_users:
                    await self.notification_service.send_boost_notification(user_id)
                    await asyncio.sleep(1)  # Не спамим
                
                # Ждем 6 часов
                await asyncio.sleep(6 * 3600)  # 6 часов
                
            except Exception as e:
                logger.error(f"Error in boost availability checks: {e}")
                await asyncio.sleep(3600)  # Ждем час при ошибке
    
    async def _get_inactive_users(self, days: int) -> List[int]:
        """Получение неактивных пользователей"""
        query = """
            SELECT id FROM users
            WHERE is_active = true
            AND last_active < NOW() - INTERVAL '%s days'
            AND is_premium = false
            LIMIT 100
        """ % days
        
        try:
            rows = await self.notification_service.db.fetch(query)
            return [row['id'] for row in rows]
        except Exception as e:
            logger.error(f"Error getting inactive users: {e}")
            return []
    
    async def _get_free_users(self) -> List[int]:
        """Получение пользователей без Premium"""
        query = """
            SELECT id FROM users
            WHERE is_active = true
            AND (is_premium = false OR premium_until < NOW())
            LIMIT 50
        """
        
        try:
            rows = await self.notification_service.db.fetch(query)
            return [row['id'] for row in rows]
        except Exception as e:
            logger.error(f"Error getting free users: {e}")
            return []
    
    async def _get_active_users_without_boost(self) -> List[int]:
        """Получение активных пользователей без буста"""
        query = """
            SELECT id FROM users
            WHERE is_active = true
            AND last_active > NOW() - INTERVAL '1 day'
            AND NOT EXISTS (
                SELECT 1 FROM user_boosts
                WHERE user_id = users.id AND expires_at > NOW()
            )
            LIMIT 30
        """
        
        try:
            rows = await self.notification_service.db.fetch(query)
            return [row['id'] for row in rows]
        except Exception as e:
            logger.error(f"Error getting active users without boost: {e}")
            return []
