# 🏗️ Flirtly - Полная архитектура системы знакомств

## 🎯 **ОБЗОР АРХИТЕКТУРЫ**

Flirtly - это полноценная система знакомств в Telegram с гибридным подходом: **Telegram Bot + Web App + Database + ML алгоритмы**.

### **📊 Архитектурная диаграмма:**

```
┌─────────────────────────────────────────────────────────┐
│                    TELEGRAM USER                         │
└────────────────────┬───────────────────────────────────┘
                     │
         ┌───────────┴────────────┐
         │                        │
    ┌────▼─────┐          ┌──────▼──────┐
    │ BOT CHAT │          │   WEB APP   │
    │          │          │             │
    │ Commands │          │ Swipe UI    │
    │ Inline   │          │ Chat UI     │
    │ Buttons  │          │ Profile UI  │
    └────┬─────┘          └──────┬──────┘
         │                       │
         └───────┬───────────────┘
                 │
    ┌────────────▼────────────┐
    │      BACKEND API        │
    │                         │
    │ • Bot Handlers          │
    │ • Web App Handlers      │
    │ • Matching Engine       │
    │ • Messaging Service     │
    │ • Notification Service  │
    └────────────┬────────────┘
                 │
    ┌────────────▼────────────┐
    │      DATA LAYER         │
    │                         │
    │ • PostgreSQL Database   │
    │ • Redis Cache           │
    │ • File Storage (R2)     │
    │ • WebSocket Server      │
    └─────────────────────────┘
```

## 🚀 **КОМПОНЕНТЫ СИСТЕМЫ**

### **1. 🤖 Telegram Bot (bot_full.py)**

**Функции:**
- **Команды**: `/start`, `/profile`, `/matches`, `/search`, `/premium`, `/settings`, `/help`
- **Inline кнопки**: Навигация, быстрые действия
- **Уведомления**: Матчи, лайки, сообщения
- **Чат**: Прямое общение между матчами
- **Web App интеграция**: Кнопки для открытия Web App

**Примеры команд:**
```python
/start - Главное меню с inline кнопками
/profile - Показ профиля с кнопками редактирования
/matches - Список матчей с кнопками чата
/search - Поиск с лимитами и Premium предложениями
/premium - Подписка с Telegram Stars
```

### **2. 📱 Web App (existing files)**

**Функции:**
- **Onboarding**: Регистрация с фото и геолокацией
- **Swipe UI**: Карточки для свайпов
- **Chat UI**: Общение с матчами
- **Profile UI**: Редактирование профиля
- **Premium UI**: Управление подпиской

### **3. 🧠 Matching Engine (matching_engine.py)**

**Умный алгоритм подбора:**

```python
# Многофакторная система оценки
weights = {
    'location': 0.25,      # географическая близость
    'interests': 0.30,     # общие интересы
    'activity': 0.15,      # активность пользователя
    'photo_quality': 0.10, # качество фото
    'popularity': 0.10,    # популярность
    'freshness': 0.10      # новизна аккаунта
}
```

**Алгоритм:**
1. **Pre-filtering**: Быстрая фильтрация по возрасту, полу, локации
2. **Scoring**: Детальный расчет совместимости
3. **Ranking**: Сортировка по score
4. **Caching**: Кэширование результатов

### **4. 💬 Messaging Service (messaging_service.py)**

**Гибридная система общения:**

```python
# Поддерживает оба канала
async def send_message(from_user, to_user, content, source):
    # 1. Сохранение в БД
    # 2. WebSocket уведомление (если онлайн в Web App)
    # 3. Telegram уведомление (если не онлайн)
    # 4. Активация Telegram чата
```

**Возможности:**
- **Web App чат**: Real-time через WebSocket
- **Telegram чат**: Прямое общение в боте
- **Уведомления**: Push в Telegram
- **История**: Сохранение всех сообщений

### **5. 🔔 Notification Service (notification_service.py)**

**Типы уведомлений:**
- **Матчи**: Новые совпадения
- **Лайки**: Кто лайкнул профиль
- **Сообщения**: Новые сообщения
- **Premium**: Предложения подписки
- **Активность**: Напоминания о возврате

**Планировщик:**
```python
# Автоматические уведомления
- Ежедневные напоминания об активности
- Еженедельные предложения Premium
- Проверки доступности бустов
```

### **6. 🗄️ Database Schema (database/schema.sql)**

**Таблицы:**
- **users**: Профили пользователей с геолокацией
- **photos**: Фото с модерацией и AI анализом
- **interests**: Интересы и категории
- **likes**: Взаимодействия (лайки/дизлайки)
- **matches**: Совпадения с алгоритмом
- **messages**: Сообщения чатов
- **referrals**: Реферальная программа
- **payments**: Платежи через Telegram Stars

**Индексы для производительности:**
```sql
-- Геолокация
CREATE INDEX idx_users_location ON users USING GIST(location);

-- Поиск кандидатов
CREATE INDEX idx_users_age_gender ON users(age, gender) WHERE is_active = true;

-- Матчи
CREATE INDEX idx_matches_user1 ON matches(user1_id);
CREATE INDEX idx_matches_user2 ON matches(user2_id);
```

## 🔄 **ПОТОКИ ДАННЫХ**

### **1. Регистрация пользователя:**
```
Web App → Bot Handler → Database → Notification
```

### **2. Swipe процесс:**
```
Web App → Like Handler → Matching Engine → Notification Service → Telegram
```

### **3. Общение:**
```
Web App/Telegram → Messaging Service → Database → WebSocket/Telegram
```

### **4. Подбор кандидатов:**
```
Web App → Matching Engine → Cache → Database → Web App
```

## 🚀 **ЗАПУСК СИСТЕМЫ**

### **1. Установка зависимостей:**
```bash
pip install python-telegram-bot asyncpg redis aiosqlite
```

### **2. Настройка окружения:**
```bash
export BOT_TOKEN="8430527446:AAFLoCZqvreDpsgz4d5z4J5LXMLC42B9ex0"
export WEBAPP_URL="https://vlamay.github.io/flirtly-webapp"
export DATABASE_URL="sqlite+aiosqlite:///./flirtly.db"
export REDIS_URL="redis://localhost:6379"
```

### **3. Инициализация базы данных:**
```bash
# Для SQLite (простая версия)
python -c "import asyncio; from database.init_db import init_sqlite; asyncio.run(init_sqlite())"

# Для PostgreSQL (production)
psql -f database/schema.sql
```

### **4. Запуск системы:**
```bash
python main.py
```

## 📊 **МОНИТОРИНГ И АНАЛИТИКА**

### **Метрики:**
- **Пользователи**: Регистрации, активность, retention
- **Матчи**: Количество, качество, конверсия
- **Сообщения**: Объем, ответы, engagement
- **Premium**: Конверсия, доход, churn

### **Логирование:**
```python
# Структурированные логи
logger.info(f"Match created: {user1_id} <-> {user2_id}, score: {score}")
logger.info(f"Message sent: {from_user} -> {to_user}, type: {source}")
logger.info(f"Premium conversion: {user_id}, type: {subscription_type}")
```

## 🔧 **КОНФИГУРАЦИЯ**

### **Переменные окружения:**
```bash
# Bot
BOT_TOKEN=your_telegram_bot_token
WEBAPP_URL=https://your-webapp-url.com

# Database
DATABASE_URL=postgresql://user:pass@host:port/db
USE_POSTGRES=true

# Cache
REDIS_URL=redis://localhost:6379

# Storage
R2_ENDPOINT=https://your-account.r2.cloudflarestorage.com
R2_ACCESS_KEY=your_access_key
R2_SECRET_KEY=your_secret_key

# Features
ENABLE_ML_MATCHING=true
ENABLE_REAL_TIME_CHAT=true
ENABLE_PREMIUM_FEATURES=true
```

### **Настройки алгоритма:**
```python
# Веса для matching
MATCHING_WEIGHTS = {
    'location': 0.25,
    'interests': 0.30,
    'activity': 0.15,
    'photo_quality': 0.10,
    'popularity': 0.10,
    'freshness': 0.10
}

# Лимиты
DAILY_LIKES_LIMIT = 10
PREMIUM_DAILY_LIKES = 999
SUPERLIKE_LIMIT = 1
PREMIUM_SUPERLIKE_LIMIT = 5
```

## 🎯 **ПРЕИМУЩЕСТВА АРХИТЕКТУРЫ**

### **✅ Telegram Bot:**
- **Команды**: Быстрый доступ к функциям
- **Inline кнопки**: Удобная навигация
- **Уведомления**: Push в Telegram
- **Чат**: Прямое общение
- **Интеграция**: Web App кнопки

### **✅ Web App:**
- **UI/UX**: Современный интерфейс
- **Swipe**: Плавные анимации
- **Real-time**: WebSocket чаты
- **Мобильность**: Адаптивный дизайн

### **✅ Умный алгоритм:**
- **Многофакторность**: 6 критериев совместимости
- **Адаптивность**: Обучение на взаимодействиях
- **Производительность**: Кэширование и индексы
- **Объяснимость**: Понятные объяснения совпадений

### **✅ Гибридное общение:**
- **Web App**: Real-time чаты
- **Telegram**: Прямое общение в боте
- **Уведомления**: Push в Telegram
- **Синхронизация**: Единая история сообщений

### **✅ Масштабируемость:**
- **PostgreSQL**: Надежная БД
- **Redis**: Быстрый кэш
- **Индексы**: Оптимизированные запросы
- **Кэширование**: Снижение нагрузки

## 🚀 **DEPLOYMENT**

### **Docker Compose:**
```yaml
version: '3.8'
services:
  app:
    build: .
    environment:
      - BOT_TOKEN=${BOT_TOKEN}
      - DATABASE_URL=postgresql://postgres:password@db:5432/flirtly
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis
  
  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=flirtly
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  redis:
    image: redis:7-alpine
  
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
```

### **Production checklist:**
- ✅ SSL сертификаты
- ✅ Database backup
- ✅ Monitoring (Prometheus/Grafana)
- ✅ Logging (ELK stack)
- ✅ CDN для статики
- ✅ Rate limiting
- ✅ Security headers

## 🎉 **РЕЗУЛЬТАТ**

**Полноценная система знакомств с:**
- 🤖 **Telegram Bot** с командами и уведомлениями
- 📱 **Web App** с современным UI/UX
- 🧠 **Умный алгоритм** подбора пар
- 💬 **Гибридное общение** (Web App + Telegram)
- 🔔 **Система уведомлений** через Telegram
- 🗄️ **Надежная БД** с оптимизацией
- 📊 **Аналитика** и мониторинг
- 🚀 **Масштабируемость** для роста

**Готово к production использованию!** 🎯✨
