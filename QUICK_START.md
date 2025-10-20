# ⚡ SparkMatch - Быстрый запуск

Инструкция по запуску твоего сервиса знакомств за 15 минут!

## 🚀 Вариант 1: Автоматический деплой (рекомендуется)

### Шаг 1: Запусти скрипт деплоя
```bash
cd /path/to/Flirtly
./deploy.sh
```

Скрипт автоматически:
- Инициализирует Git репозиторий
- Настроит remote origin
- Отправит код в GitHub
- Покажет URL для настройки в BotFather

### Шаг 2: Настрой BotFather
1. Перейди в @BotFather
2. `/mybots` → выбери бота
3. `Mini Apps` → `Menu Button` → `Set URL`
4. Введи URL который показал скрипт
5. Сохрани

**Готово!** 🎉

---

## 🛠 Вариант 2: Ручной деплой

### Шаг 1: Создай репозиторий на GitHub
1. Зайди на github.com
2. Нажми "New repository"
3. Название: `sparkmatch-webapp`
4. Сделай публичным
5. Создай репозиторий

### Шаг 2: Загрузи код
```bash
cd /path/to/Flirtly
git init
git add .
git commit -m "🚀 Initial commit: SparkMatch Web App"
git branch -M main
git remote add origin https://github.com/ТВОЙ_USERNAME/sparkmatch-webapp.git
git push -u origin main
```

### Шаг 3: Включи GitHub Pages
1. Перейди в Settings репозитория
2. `Pages` → `Source: Deploy from a branch`
3. `Branch: main`
4. `Save`

### Шаг 4: Настрой BotFather
1. @BotFather → `/mybots`
2. Выбери бота → `Mini Apps`
3. `Menu Button` → `Set URL`
4. URL: `https://ТВОЙ_USERNAME.github.io/sparkmatch-webapp/`

---

## 🎯 Вариант 3: Локальное тестирование

### Если хочешь сначала протестировать локально:

```bash
# Запусти простой HTTP сервер
python3 -m http.server 8000

# Или если у тебя Node.js
npx serve .

# Или если у тебя PHP
php -S localhost:8000
```

Открой: `http://localhost:8000`

**Для тестирования в Telegram:**
1. Используй ngrok для туннеля:
```bash
npx ngrok http 8000
```
2. Скопируй HTTPS URL
3. Настрой в BotFather

---

## 📱 Быстрое тестирование

### После настройки BotFather:

1. **Открой бота** в Telegram
2. **Отправь**: `/start`
3. **Найди кнопку Web App** в меню
4. **Протестируй**:
   - ✅ Загрузка профилей
   - ✅ Swipe влево/вправо
   - ✅ Кнопки лайк/суперлайк
   - ✅ Анимации

### Что должно работать:
- 🎨 Красивый интерфейс с градиентами
- 📱 Swipe жесты на мобильном
- ⚡ Плавные анимации
- 💕 Счетчики лайков и совпадений
- 🌙 Поддержка темной темы

---

## 🚨 Решение проблем

### Web App не открывается:
```bash
# Проверь статус GitHub Pages
curl -I https://ТВОЙ_USERNAME.github.io/sparkmatch-webapp/
```

### Ошибка 404:
- Убедись что репозиторий публичный
- Проверь что GitHub Pages включены
- Подожди 5-10 минут после включения

### Не работают swipe жесты:
- Используй мобильное устройство
- Проверь что JavaScript включен
- Убедись что используешь современный браузер

---

## 🎉 Готово!

Твой SparkMatch Web App готов! 

**Что дальше:**
1. 🎨 Создай красивый аватар бота
2. 📢 Пригласи первых пользователей
3. 💰 Настрой систему платежей
4. 📊 Добавь аналитику

**Время до запуска: 15 минут** ⚡

---

## 💡 Полезные ссылки

- [Telegram Web Apps Documentation](https://core.telegram.org/bots/webapps)
- [GitHub Pages Documentation](https://pages.github.com/)
- [PWA Documentation](https://web.dev/progressive-web-apps/)

**Удачи в создании успешного сервиса знакомств!** 💕
