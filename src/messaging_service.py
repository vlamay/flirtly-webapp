# messaging_service.py - Система сообщений для Telegram и Web App

import asyncio
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import json
import uuid

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

logger = logging.getLogger(__name__)

@dataclass
class Message:
    id: int
    match_id: int
    sender_id: int
    content: str
    message_type: str = 'text'
    media_url: Optional[str] = None
    is_read: bool = False
    created_at: datetime

@dataclass
class ChatSession:
    match_id: int
    user1_id: int
    user2_id: int
    last_message_at: Optional[datetime]
    unread_count_user1: int = 0
    unread_count_user2: int = 0
    is_active: bool = True

class MessagingService:
    def __init__(self, bot, db_connection, cache_service=None, websocket_service=None):
        self.bot = bot
        self.db = db_connection
        self.cache = cache_service
        self.websocket = websocket_service
        self.active_chats = {}  # In-memory cache для активных чатов
    
    async def send_message(self, from_user: int, to_user: int, content: str, 
                          source: str = 'webapp', message_type: str = 'text',
                          media_url: Optional[str] = None) -> Optional[Message]:
        """Универсальная отправка сообщений"""
        
        try:
            # 1. Находим или создаем матч
            match = await self._get_or_create_match(from_user, to_user)
            if not match:
                logger.error(f"No match found between users {from_user} and {to_user}")
                return None
            
            # 2. Сохраняем сообщение в базу
            message = await self._save_message(
                match_id=match['id'],
                sender_id=from_user,
                content=content,
                message_type=message_type,
                media_url=media_url
            )
            
            # 3. Обновляем статистику чата
            await self._update_chat_stats(match['id'], from_user, to_user)
            
            # 4. Real-time доставка через WebSocket (если пользователь онлайн в WebApp)
            if self.websocket:
                await self._send_websocket_notification(to_user, message)
            
            # 5. Telegram уведомление (если пользователь не онлайн в WebApp)
            if not await self._is_user_in_webapp(to_user):
                await self._send_telegram_notification(to_user, from_user, content, match['id'])
            
            # 6. Активируем режим чата в Telegram
            await self._activate_telegram_chat_mode(from_user, to_user)
            
            logger.info(f"Message sent from {from_user} to {to_user}: {content[:50]}...")
            return message
            
        except Exception as e:
            logger.error(f"Error sending message from {from_user} to {to_user}: {e}")
            return None
    
    async def get_chat_messages(self, user_id: int, match_id: int, limit: int = 50) -> List[Message]:
        """Получение сообщений чата"""
        
        query = """
            SELECT 
                m.id, m.match_id, m.sender_id, m.content, m.message_type,
                m.media_url, m.is_read, m.created_at,
                u.name as sender_name
            FROM messages m
            JOIN users u ON m.sender_id = u.id
            WHERE m.match_id = $1
            ORDER BY m.created_at DESC
            LIMIT $2
        """
        
        try:
            rows = await self.db.fetch(query, match_id, limit)
            messages = []
            
            for row in rows:
                message = Message(
                    id=row['id'],
                    match_id=row['match_id'],
                    sender_id=row['sender_id'],
                    content=row['content'],
                    message_type=row['message_type'],
                    media_url=row['media_url'],
                    is_read=row['is_read'],
                    created_at=row['created_at']
                )
                messages.append(message)
            
            return list(reversed(messages))  # Возвращаем в хронологическом порядке
            
        except Exception as e:
            logger.error(f"Error getting chat messages for match {match_id}: {e}")
            return []
    
    async def get_user_chats(self, user_id: int) -> List[ChatSession]:
        """Получение всех чатов пользователя"""
        
        query = """
            SELECT 
                m.id as match_id,
                CASE 
                    WHEN m.user1_id = $1 THEN m.user2_id
                    ELSE m.user1_id
                END as partner_id,
                u.name as partner_name,
                u.age as partner_age,
                u.city as partner_city,
                u.is_premium as partner_premium,
                p.medium_url as partner_photo,
                m.last_message_at,
                m.is_active,
                COUNT(msg.id) as unread_count
            FROM matches m
            JOIN users u ON (
                CASE 
                    WHEN m.user1_id = $1 THEN m.user2_id
                    ELSE m.user1_id
                END = u.id
            )
            LEFT JOIN photos p ON u.id = p.user_id AND p.position = 0 AND p.moderation_status = 'approved'
            LEFT JOIN messages msg ON m.id = msg.match_id 
                AND msg.sender_id != $1 
                AND msg.is_read = false
            WHERE (m.user1_id = $1 OR m.user2_id = $1)
            AND m.is_active = true
            GROUP BY m.id, m.user1_id, m.user2_id, u.name, u.age, u.city, 
                     u.is_premium, p.medium_url, m.last_message_at, m.is_active
            ORDER BY m.last_message_at DESC NULLS LAST
        """
        
        try:
            rows = await self.db.fetch(query, user_id)
            chats = []
            
            for row in rows:
                chat = ChatSession(
                    match_id=row['match_id'],
                    user1_id=user_id,
                    user2_id=row['partner_id'],
                    last_message_at=row['last_message_at'],
                    unread_count_user1=row['unread_count'],
                    is_active=row['is_active']
                )
                chats.append(chat)
            
            return chats
            
        except Exception as e:
            logger.error(f"Error getting user chats for user {user_id}: {e}")
            return []
    
    async def mark_messages_as_read(self, user_id: int, match_id: int):
        """Отметить сообщения как прочитанные"""
        
        query = """
            UPDATE messages 
            SET is_read = true, read_at = NOW()
            WHERE match_id = $1 AND sender_id != $2 AND is_read = false
        """
        
        try:
            await self.db.execute(query, match_id, user_id)
            logger.info(f"Messages marked as read for user {user_id} in match {match_id}")
        except Exception as e:
            logger.error(f"Error marking messages as read: {e}")
    
    async def handle_telegram_message(self, update: Update, context):
        """Обработка сообщений в Telegram чате"""
        
        user_id = update.effective_user.id
        message_text = update.message.text
        
        # Проверяем есть ли активный чат
        active_chat = await self.get_active_telegram_chat(user_id)
        
        if active_chat:
            # Пересылаем сообщение матчу
            success = await self.send_message(
                from_user=user_id,
                to_user=active_chat['partner_id'],
                content=message_text,
                source='telegram'
            )
            
            if success:
                await update.message.reply_text("✅ Сообщение отправлено!")
            else:
                await update.message.reply_text("❌ Ошибка отправки сообщения")
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
    
    async def start_telegram_chat(self, user_id: int, match_id: int):
        """Начать чат в Telegram с конкретным матчем"""
        
        # Получаем информацию о матче
        match_info = await self._get_match_info(user_id, match_id)
        if not match_info:
            return False
        
        # Активируем режим чата
        await self._activate_telegram_chat_mode(user_id, match_info['partner_id'])
        
        # Отправляем уведомление пользователю
        try:
            await self.bot.send_message(
                chat_id=user_id,
                text=f"💬 <b>Чат с {match_info['partner_name']}</b>\n\n"
                     f"Теперь ты можешь писать сообщения прямо здесь!\n"
                     f"Или открой Web App для удобного общения.",
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("⚡ Открыть в Web App", 
                                       web_app=WebAppInfo(url=f"{self.webapp_url}/chat/{match_id}"))]
                ])
            )
        except Exception as e:
            logger.error(f"Error sending chat notification to {user_id}: {e}")
        
        return True
    
    # ===================================
    # PRIVATE METHODS
    # ===================================
    
    async def _get_or_create_match(self, user1_id: int, user2_id: int) -> Optional[Dict]:
        """Найти или создать матч между пользователями"""
        
        # Проверяем существующий матч
        query = """
            SELECT id, user1_id, user2_id, is_active
            FROM matches
            WHERE (user1_id = $1 AND user2_id = $2) OR (user1_id = $2 AND user2_id = $1)
        """
        
        match = await self.db.fetchrow(query, user1_id, user2_id)
        
        if match:
            return {
                'id': match['id'],
                'user1_id': match['user1_id'],
                'user2_id': match['user2_id'],
                'is_active': match['is_active']
            }
        
        # Создаем новый матч
        try:
            insert_query = """
                INSERT INTO matches (user1_id, user2_id, created_at)
                VALUES ($1, $2, NOW())
                RETURNING id
            """
            
            # Убеждаемся что user1_id < user2_id для уникальности
            id1, id2 = sorted([user1_id, user2_id])
            
            match_id = await self.db.fetchval(insert_query, id1, id2)
            
            return {
                'id': match_id,
                'user1_id': id1,
                'user2_id': id2,
                'is_active': True
            }
            
        except Exception as e:
            logger.error(f"Error creating match between {user1_id} and {user2_id}: {e}")
            return None
    
    async def _save_message(self, match_id: int, sender_id: int, content: str,
                           message_type: str = 'text', media_url: Optional[str] = None) -> Message:
        """Сохранение сообщения в базу данных"""
        
        query = """
            INSERT INTO messages (match_id, sender_id, content, message_type, media_url, created_at)
            VALUES ($1, $2, $3, $4, $5, NOW())
            RETURNING id, match_id, sender_id, content, message_type, media_url, is_read, created_at
        """
        
        row = await self.db.fetchrow(query, match_id, sender_id, content, message_type, media_url)
        
        return Message(
            id=row['id'],
            match_id=row['match_id'],
            sender_id=row['sender_id'],
            content=row['content'],
            message_type=row['message_type'],
            media_url=row['media_url'],
            is_read=row['is_read'],
            created_at=row['created_at']
        )
    
    async def _update_chat_stats(self, match_id: int, sender_id: int, recipient_id: int):
        """Обновление статистики чата"""
        
        # Обновляем время последнего сообщения
        query = """
            UPDATE matches 
            SET last_message_at = NOW()
            WHERE id = $1
        """
        await self.db.execute(query, match_id)
        
        # Обновляем счетчики непрочитанных
        unread_query = """
            UPDATE users 
            SET unread_messages_count = (
                SELECT COUNT(*) FROM messages m
                JOIN matches mt ON m.match_id = mt.id
                WHERE (mt.user1_id = $1 OR mt.user2_id = $1)
                AND m.sender_id != $1
                AND m.is_read = false
            )
            WHERE id = $1
        """
        await self.db.execute(unread_query, recipient_id)
    
    async def _send_websocket_notification(self, user_id: int, message: Message):
        """Отправка уведомления через WebSocket"""
        
        if self.websocket:
            try:
                await self.websocket.send_to_user(user_id, {
                    'type': 'new_message',
                    'message': {
                        'id': message.id,
                        'match_id': message.match_id,
                        'sender_id': message.sender_id,
                        'content': message.content,
                        'message_type': message.message_type,
                        'media_url': message.media_url,
                        'created_at': message.created_at.isoformat()
                    }
                })
            except Exception as e:
                logger.error(f"Error sending websocket notification: {e}")
    
    async def _send_telegram_notification(self, user_id: int, sender_id: int, 
                                        content: str, match_id: int):
        """Отправка уведомления через Telegram"""
        
        try:
            # Получаем информацию об отправителе
            sender_info = await self.db.fetchrow(
                "SELECT name, age FROM users WHERE id = $1", sender_id
            )
            
            if not sender_info:
                return
            
            sender_name = sender_info['name']
            sender_age = sender_info['age']
            
            # Обрезаем сообщение для уведомления
            preview = content[:100] + "..." if len(content) > 100 else content
            
            keyboard = [
                [InlineKeyboardButton("💬 Ответить в Web App", 
                                   web_app=WebAppInfo(url=f"{self.webapp_url}/chat/{match_id}"))],
                [InlineKeyboardButton("✍️ Ответить здесь", callback_data=f"reply_{match_id}")]
            ]
            
            await self.bot.send_message(
                chat_id=user_id,
                text=f"💬 <b>Новое сообщение от {sender_name}, {sender_age}</b>\n\n{preview}",
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            
        except Exception as e:
            logger.error(f"Error sending telegram notification: {e}")
    
    async def _activate_telegram_chat_mode(self, user1_id: int, user2_id: int):
        """Активация режима чата в Telegram"""
        
        if self.cache:
            # Сохраняем в Redis на 1 час
            await self.cache.set(f"telegram_chat:{user1_id}", user2_id, ttl=3600)
            await self.cache.set(f"telegram_chat:{user2_id}", user1_id, ttl=3600)
        
        # Также сохраняем в памяти
        self.active_chats[user1_id] = user2_id
        self.active_chats[user2_id] = user1_id
    
    async def get_active_telegram_chat(self, user_id: int) -> Optional[Dict]:
        """Получение активного чата в Telegram"""
        
        # Сначала проверяем кэш
        if self.cache:
            partner_id = await self.cache.get(f"telegram_chat:{user_id}")
            if partner_id:
                return {'partner_id': int(partner_id)}
        
        # Затем память
        if user_id in self.active_chats:
            return {'partner_id': self.active_chats[user_id]}
        
        return None
    
    async def _is_user_in_webapp(self, user_id: int) -> bool:
        """Проверка онлайн ли пользователь в Web App"""
        
        if self.cache:
            return await self.cache.exists(f"webapp_online:{user_id}")
        
        return False
    
    async def _get_match_info(self, user_id: int, match_id: int) -> Optional[Dict]:
        """Получение информации о матче"""
        
        query = """
            SELECT 
                m.id,
                CASE 
                    WHEN m.user1_id = $1 THEN m.user2_id
                    ELSE m.user1_id
                END as partner_id,
                u.name as partner_name,
                u.age as partner_age
            FROM matches m
            JOIN users u ON (
                CASE 
                    WHEN m.user1_id = $1 THEN m.user2_id
                    ELSE m.user1_id
                END = u.id
            )
            WHERE m.id = $2 AND (m.user1_id = $1 OR m.user2_id = $1)
        """
        
        try:
            row = await self.db.fetchrow(query, user_id, match_id)
            if row:
                return {
                    'id': row['id'],
                    'partner_id': row['partner_id'],
                    'partner_name': row['partner_name'],
                    'partner_age': row['partner_age']
                }
            return None
        except Exception as e:
            logger.error(f"Error getting match info: {e}")
            return None

# WebSocket Service для real-time сообщений
class WebSocketService:
    def __init__(self):
        self.connections = {}  # user_id -> websocket
    
    async def connect(self, user_id: int, websocket):
        """Подключение пользователя к WebSocket"""
        self.connections[user_id] = websocket
        logger.info(f"User {user_id} connected to websocket")
    
    async def disconnect(self, user_id: int):
        """Отключение пользователя от WebSocket"""
        if user_id in self.connections:
            del self.connections[user_id]
            logger.info(f"User {user_id} disconnected from websocket")
    
    async def send_to_user(self, user_id: int, data: Dict[str, Any]):
        """Отправка данных пользователю"""
        if user_id in self.connections:
            try:
                websocket = self.connections[user_id]
                await websocket.send_text(json.dumps(data))
            except Exception as e:
                logger.error(f"Error sending websocket message to {user_id}: {e}")
                await self.disconnect(user_id)
    
    async def broadcast_to_match(self, match_id: int, data: Dict[str, Any]):
        """Отправка данных всем участникам матча"""
        # Получаем участников матча
        # И отправляем каждому
        pass
