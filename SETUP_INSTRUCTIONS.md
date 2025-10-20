# 🚀 SparkMatch Web App - Инструкции по настройке

## 📋 Информация о проекте

- **GitHub репозиторий**: https://github.com/vlamay/flirtly-webapp
- **Telegram бот**: @FFlirtly_bot
- **Bot Token**: 8430527446:AAFLoCZqvreDpsgz4d5z4J5LXMLC42B9ex0
- **URL после настройки**: https://vlamay.github.io/flirtly-webapp/

## 🔧 Шаг 1: Включение GitHub Pages

### Автоматически (рекомендуется):
1. Перейди в https://github.com/vlamay/flirtly-webapp
2. Нажми **Settings** (вкладка справа)
3. Прокрути вниз до раздела **Pages**
4. В разделе **Source** выбери **Deploy from a branch**
5. В разделе **Branch** выбери **main**
6. Нажми **Save**
7. Подожди 5-10 минут

### Проверка:
После включения Pages, твой Web App будет доступен по адресу:
```
https://vlamay.github.io/flirtly-webapp/
```

## 🤖 Шаг 2: Настройка BotFather

### Настройка Mini App:
1. Открой @BotFather в Telegram
2. Отправь команду `/mybots`
3. Выбери бота **@FFlirtly_bot**
4. Нажми **Mini Apps**
5. Нажми **Menu Button**
6. Выбери **Set URL**
7. Введи URL: `https://vlamay.github.io/flirtly-webapp/`
8. Нажми **Send**

### Дополнительные настройки:
1. **Аватар бота**: `/mybots` → @FFlirtly_bot → **Edit Bot** → **Edit Botpic**
   - Загрузи фото 512x512 с логотипом ⚡
2. **Welcome Picture**: **Edit Bot** → **Welcome Picture**
   - Загрузи баннер 640x360 с описанием сервиса

## 🧪 Шаг 3: Тестирование

### После настройки BotFather:
1. Открой бота @FFlirtly_bot в Telegram
2. Отправь команду `/start`
3. Найди кнопку **Web App** в меню
4. Нажми на неё - должен открыться красивый интерфейс
5. Протестируй все функции:
   - ✅ Swipe жесты (влево/вправо)
   - ✅ Кнопки лайк/суперлайк/пропуск
   - ✅ Анимации и эффекты
   - ✅ Счетчики лайков и совпадений

## 🔗 Интеграция с ботом

### В коде бота добавь обработчик Web App данных:

```python
from telegram import Update
from telegram.ext import ContextTypes
import json

async def handle_web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка данных от Web App"""
    web_app_data = update.effective_message.web_app_data.data
    
    try:
        data = json.loads(web_app_data)
        action = data.get('action')
        profile_id = data.get('profile_id')
        user_id = data.get('user_id')
        
        if action == 'like':
            await handle_like(user_id, profile_id)
        elif action == 'skip':
            await handle_skip(user_id, profile_id)
        elif action == 'superlike':
            await handle_superlike(user_id, profile_id)
            
        await update.effective_message.reply_text(
            f"✅ {action} обработан для профиля {profile_id}"
        )
        
    except Exception as e:
        await update.effective_message.reply_text(
            f"❌ Ошибка обработки: {str(e)}"
        )

# Добавь в application:
application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_web_app_data))
```

## 🎯 Что дальше?

### Краткосрочные задачи:
1. 🎨 Создай красивый аватар бота
2. 📢 Пригласи первых пользователей
3. 💬 Собери фидбек
4. 💰 Настрой систему платежей

### Среднесрочные задачи:
1. 👥 Добавь реальные профили из БД
2. 💬 Интегрируй систему чатов
3. 📊 Добавь аналитику
4. 🔍 Создай фильтры поиска

## 🚨 Решение проблем

### Web App не открывается:
- Проверь что GitHub Pages включены
- Убедись что URL правильный в BotFather
- Подожди 5-10 минут после включения Pages

### Ошибки в консоли:
- Открой DevTools в браузере
- Проверь Network tab на ошибки
- Убедись что все файлы загружаются

### Не работают swipe жесты:
- Используй мобильное устройство
- Проверь поддержку touch событий
- Убедись что JavaScript включен

## 📱 Особенности Web App

- **Современный дизайн** с градиентами и анимациями
- **Swipe жесты** для интуитивного управления
- **Интерактивные карточки** профилей
- **Система лайков** и суперлайков
- **PWA поддержка** для работы как приложение
- **Темная тема** для интеграции с Telegram

## 🎉 Готово!

После выполнения всех шагов твой SparkMatch Web App будет полностью готов к использованию!

**URL Web App**: https://vlamay.github.io/flirtly-webapp/
**Telegram бот**: @FFlirtly_bot

Удачи в создании успешного сервиса знакомств! ⚡💕
