# main.py - Главный файл запуска полноценной системы Flirtly

import asyncio
import logging
import os
import sys
from pathlib import Path

# Добавляем src в путь
sys.path.append(str(Path(__file__).parent / "src"))

from bot_full import FlirtlyBot
from matching_engine import MatchingEngine
from messaging_service import MessagingService, WebSocketService
from notification_service import NotificationService, NotificationScheduler

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class FlirtlyApp:
    def __init__(self):
        self.bot_token = os.getenv("BOT_TOKEN", "8430527446:AAFLoCZqvreDpsgz4d5z4J5LXMLC42B9ex0")
        self.webapp_url = os.getenv("WEBAPP_URL", "https://vlamay.github.io/flirtly-webapp")
        self.database_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./flirtly.db")
        
        # Инициализация компонентов
        self.bot = None
        self.db = None
        self.cache = None
        self.websocket = None
        
        # Сервисы
        self.matching_engine = None
        self.messaging_service = None
        self.notification_service = None
        self.notification_scheduler = None
    
    async def initialize_database(self):
        """Инициализация базы данных"""
        try:
            # Для SQLite (простая версия)
            if self.database_url.startswith("sqlite"):
                import aiosqlite
                self.db = await aiosqlite.connect("flirtly.db")
                logger.info("SQLite database connected")
            
            # Для PostgreSQL (production версия)
            elif self.database_url.startswith("postgresql"):
                import asyncpg
                self.db = await asyncpg.connect(self.database_url)
                logger.info("PostgreSQL database connected")
            
            else:
                raise ValueError(f"Unsupported database URL: {self.database_url}")
                
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise
    
    async def initialize_cache(self):
        """Инициализация кэша (Redis)"""
        try:
            import redis.asyncio as redis
            
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
            self.cache = redis.from_url(redis_url)
            
            # Тестируем подключение
            await self.cache.ping()
            logger.info("Redis cache connected")
            
        except Exception as e:
            logger.warning(f"Redis cache not available: {e}")
            self.cache = None
    
    async def initialize_services(self):
        """Инициализация всех сервисов"""
        
        # WebSocket сервис
        self.websocket = WebSocketService()
        
        # Matching Engine
        self.matching_engine = MatchingEngine(self.db, self.cache)
        
        # Messaging Service
        self.messaging_service = MessagingService(
            bot=self.bot,
            db_connection=self.db,
            cache_service=self.cache,
            websocket_service=self.websocket
        )
        
        # Notification Service
        self.notification_service = NotificationService(
            bot=self.bot,
            db_connection=self.db,
            cache_service=self.cache
        )
        
        # Notification Scheduler
        self.notification_scheduler = NotificationScheduler(self.notification_service)
        
        logger.info("All services initialized")
    
    async def setup_webhook_handlers(self):
        """Настройка обработчиков WebHook"""
        
        # Добавляем обработчики для Web App данных
        @self.bot.app.message_handler(content_types=['web_app_data'])
        async def handle_webapp_data(message):
            """Обработка данных из Web App"""
            try:
                import json
                data = json.loads(message.web_app_data.data)
                action = data.get('action')
                
                if action == 'register':
                    await self._handle_registration(message, data)
                elif action == 'like':
                    await self._handle_like(message, data)
                elif action == 'superlike':
                    await self._handle_superlike(message, data)
                elif action == 'skip':
                    await self._handle_skip(message, data)
                elif action == 'message':
                    await self._handle_message(message, data)
                elif action == 'update_location':
                    await self._handle_location_update(message, data)
                
            except Exception as e:
                logger.error(f"Error handling webapp data: {e}")
        
        logger.info("WebHook handlers set up")
    
    async def _handle_registration(self, message, data):
        """Обработка регистрации из Web App"""
        try:
            telegram_id = message.from_user.id
            
            # Создаем пользователя в базе данных
            query = """
                INSERT INTO users (
                    telegram_id, username, first_name, name, age, gender,
                    looking_for, bio, city, country, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, NOW())
                ON CONFLICT (telegram_id) DO UPDATE SET
                    name = EXCLUDED.name,
                    age = EXCLUDED.age,
                    gender = EXCLUDED.gender,
                    looking_for = EXCLUDED.looking_for,
                    bio = EXCLUDED.bio,
                    city = EXCLUDED.city,
                    country = EXCLUDED.country,
                    updated_at = NOW()
                RETURNING id
            """
            
            user_id = await self.db.fetchval(
                query,
                telegram_id,
                message.from_user.username,
                message.from_user.first_name,
                data.get('name'),
                data.get('age'),
                data.get('gender'),
                data.get('looking_for'),
                data.get('bio'),
                data.get('city'),
                data.get('country')
            )
            
            # Обрабатываем фото
            photos = data.get('photos', [])
            for i, photo_url in enumerate(photos):
                photo_query = """
                    INSERT INTO photos (user_id, original_url, position, moderation_status)
                    VALUES ($1, $2, $3, 'approved')
                """
                await self.db.execute(photo_query, user_id, photo_url, i)
            
            # Обрабатываем интересы
            interests = data.get('interests', [])
            for interest_name in interests:
                # Находим ID интереса
                interest_id = await self.db.fetchval(
                    "SELECT id FROM interests WHERE name = $1", interest_name
                )
                if interest_id:
                    await self.db.execute(
                        "INSERT INTO user_interests (user_id, interest_id) VALUES ($1, $2)",
                        user_id, interest_id
                    )
            
            # Отправляем подтверждение
            await message.reply_text(
                "🎉 <b>Регистрация завершена!</b>\n\n"
                "Добро пожаловать в Flirtly! Теперь ты можешь начать искать совпадения! ⚡",
                parse_mode='HTML'
            )
            
            logger.info(f"User {telegram_id} registered successfully")
            
        except Exception as e:
            logger.error(f"Error handling registration: {e}")
            await message.reply_text("❌ Ошибка регистрации. Попробуйте еще раз.")
    
    async def _handle_like(self, message, data):
        """Обработка лайка из Web App"""
        try:
            from_user_id = message.from_user.id
            to_user_id = data.get('user_id')
            
            # Получаем ID пользователя из telegram_id
            from_user_db_id = await self.db.fetchval(
                "SELECT id FROM users WHERE telegram_id = $1", from_user_id
            )
            
            if not from_user_db_id:
                await message.reply_text("❌ Пользователь не найден")
                return
            
            # Создаем лайк
            like_query = """
                INSERT INTO likes (from_user_id, to_user_id, action, created_at)
                VALUES ($1, $2, 'like', NOW())
                ON CONFLICT (from_user_id, to_user_id) DO UPDATE SET
                    action = 'like',
                    created_at = NOW()
            """
            await self.db.execute(like_query, from_user_db_id, to_user_id)
            
            # Проверяем взаимность
            mutual_like = await self.db.fetchval(
                "SELECT 1 FROM likes WHERE from_user_id = $1 AND to_user_id = $2 AND action IN ('like', 'superlike')",
                to_user_id, from_user_db_id
            )
            
            if mutual_like:
                # Создаем матч
                match_query = """
                    INSERT INTO matches (user1_id, user2_id, created_at)
                    VALUES ($1, $2, NOW())
                    ON CONFLICT (user1_id, user2_id) DO NOTHING
                """
                await self.db.execute(match_query, 
                                    min(from_user_db_id, to_user_id),
                                    max(from_user_db_id, to_user_id))
                
                # Отправляем уведомления
                await self.notification_service.send_match_notification(from_user_id, to_user_id)
                await self.notification_service.send_match_notification(to_user_id, from_user_id)
                
                await message.reply_text("🎉 <b>Это Match!</b>\n\nВы понравились друг другу!")
            else:
                # Отправляем уведомление о лайке
                await self.notification_service.send_like_notification(to_user_id, from_user_db_id)
                await message.reply_text("❤️ Лайк отправлен!")
            
            logger.info(f"Like processed: {from_user_db_id} -> {to_user_id}")
            
        except Exception as e:
            logger.error(f"Error handling like: {e}")
            await message.reply_text("❌ Ошибка отправки лайка")
    
    async def _handle_superlike(self, message, data):
        """Обработка суперлайка"""
        # Аналогично лайку, но с action = 'superlike'
        await self._handle_like(message, {**data, 'action': 'superlike'})
    
    async def _handle_skip(self, message, data):
        """Обработка пропуска"""
        try:
            from_user_id = message.from_user.id
            to_user_id = data.get('user_id')
            
            from_user_db_id = await self.db.fetchval(
                "SELECT id FROM users WHERE telegram_id = $1", from_user_id
            )
            
            if from_user_db_id:
                skip_query = """
                    INSERT INTO likes (from_user_id, to_user_id, action, created_at)
                    VALUES ($1, $2, 'dislike', NOW())
                    ON CONFLICT (from_user_id, to_user_id) DO UPDATE SET
                        action = 'dislike',
                        created_at = NOW()
                """
                await self.db.execute(skip_query, from_user_db_id, to_user_id)
            
            logger.info(f"Skip processed: {from_user_db_id} -> {to_user_id}")
            
        except Exception as e:
            logger.error(f"Error handling skip: {e}")
    
    async def _handle_message(self, message, data):
        """Обработка сообщения из Web App"""
        try:
            from_user_id = message.from_user.id
            to_user_id = data.get('to_user_id')
            content = data.get('content')
            
            # Используем messaging service
            result = await self.messaging_service.send_message(
                from_user=from_user_id,
                to_user=to_user_id,
                content=content,
                source='webapp'
            )
            
            if result:
                await message.reply_text("✅ Сообщение отправлено!")
            else:
                await message.reply_text("❌ Ошибка отправки сообщения")
                
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            await message.reply_text("❌ Ошибка отправки сообщения")
    
    async def _handle_location_update(self, message, data):
        """Обработка обновления геолокации"""
        try:
            telegram_id = message.from_user.id
            latitude = data.get('latitude')
            longitude = data.get('longitude')
            city = data.get('city')
            
            if latitude and longitude:
                location_query = """
                    UPDATE users 
                    SET location = ST_Point($1, $2), city = $3, updated_at = NOW()
                    WHERE telegram_id = $4
                """
                await self.db.execute(location_query, longitude, latitude, city, telegram_id)
            
            logger.info(f"Location updated for user {telegram_id}")
            
        except Exception as e:
            logger.error(f"Error handling location update: {e}")
    
    async def start(self):
        """Запуск приложения"""
        try:
            logger.info("Starting Flirtly App...")
            
            # Инициализация компонентов
            await self.initialize_database()
            await self.initialize_cache()
            
            # Инициализация бота
            self.bot = FlirtlyBot(self.bot_token, self.webapp_url)
            
            # Инициализация сервисов
            await self.initialize_services()
            
            # Настройка WebHook обработчиков
            await self.setup_webhook_handlers()
            
            # Запуск планировщика уведомлений
            if self.notification_scheduler:
                asyncio.create_task(self.notification_scheduler.start())
            
            logger.info("Flirtly App started successfully!")
            
            # Запуск бота
            self.bot.run()
            
        except Exception as e:
            logger.error(f"Failed to start Flirtly App: {e}")
            raise
    
    async def stop(self):
        """Остановка приложения"""
        try:
            logger.info("Stopping Flirtly App...")
            
            if self.notification_scheduler:
                await self.notification_scheduler.stop()
            
            if self.cache:
                await self.cache.close()
            
            if self.db:
                await self.db.close()
            
            logger.info("Flirtly App stopped")
            
        except Exception as e:
            logger.error(f"Error stopping Flirtly App: {e}")

async def main():
    """Главная функция"""
    app = FlirtlyApp()
    
    try:
        await app.start()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    except Exception as e:
        logger.error(f"Application error: {e}")
    finally:
        await app.stop()

if __name__ == "__main__":
    asyncio.run(main())
