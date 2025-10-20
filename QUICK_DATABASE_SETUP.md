# 🚀 Быстрая настройка базы данных

## 📋 ПРОСТОЙ СПОСОБ (БЕЗ VENV)

### 1. Установи зависимости глобально
```bash
# Установи необходимые пакеты
pip3 install sqlalchemy aiosqlite aiogram python-dotenv

# Или используй requirements.txt
pip3 install -r requirements.txt
```

### 2. Создай базу данных
```bash
cd /media/devops/d4f26f11-8547-4fa7-9e6b-ea0ffec5809f/Cursor/Flirtly

# Создай базу данных
python3 -c "
import asyncio
from src.database import init_db
asyncio.run(init_db())
print('✅ База данных создана!')
"
```

### 3. Запусти бота
```bash
# Запусти оптимизированного бота
python3 src/bot_optimized.py
```

## 🐳 ALTERNATIVE: Docker PostgreSQL

### 1. Запусти PostgreSQL
```bash
# Запусти PostgreSQL через Docker
docker-compose up -d postgres

# Проверь что запустилось
docker ps
```

### 2. Настрой переменные
```bash
# Создай .env файл
echo "USE_POSTGRES=true" > .env
echo "POSTGRES_HOST=localhost" >> .env
echo "POSTGRES_PORT=5432" >> .env
echo "POSTGRES_DB=flirtly" >> .env
echo "POSTGRES_USER=flirtly_user" >> .env
echo "POSTGRES_PASSWORD=flirtly_secure_password_2024" >> .env
```

### 3. Запусти бота с PostgreSQL
```bash
python3 src/bot_optimized.py
```

## 🧪 ТЕСТИРОВАНИЕ

### Проверь что база создалась
```bash
# Для SQLite
ls -la flirtly.db

# Для PostgreSQL
docker exec flirtly_postgres psql -U flirtly_user -d flirtly -c "\dt"
```

### Тест в Telegram
1. Открой @FFlirtly_bot
2. Отправь /start
3. Нажми "⚡ Открыть Flirtly"
4. Пройди регистрацию
5. Проверь что данные сохранились

## 🎯 РЕКОМЕНДАЦИЯ

**Для быстрого старта используй SQLite:**
- ✅ Простота установки
- ✅ Не требует Docker
- ✅ Идеально для MVP
- ✅ Легко мигрировать на PostgreSQL потом

**Для продакшена используй PostgreSQL:**
- 🐘 Мощность и масштабируемость
- 📊 Лучшая производительность
- 🔄 Поддержка параллельных запросов
- 📈 Готовность к росту
