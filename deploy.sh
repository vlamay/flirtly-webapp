#!/bin/bash

# SparkMatch Web App Deployment Script
# Скрипт для быстрого деплоя на GitHub Pages

echo "🚀 SparkMatch Web App Deployment Script"
echo "========================================"

# Проверка наличия Git
if ! command -v git &> /dev/null; then
    echo "❌ Git не установлен. Установите Git и попробуйте снова."
    exit 1
fi

# Получение URL репозитория
read -p "📝 Введите URL вашего GitHub репозитория (например: https://github.com/username/sparkmatch-webapp.git): " REPO_URL

if [ -z "$REPO_URL" ]; then
    echo "❌ URL репозитория не может быть пустым!"
    exit 1
fi

# Инициализация Git (если еще не инициализирован)
if [ ! -d ".git" ]; then
    echo "📦 Инициализация Git репозитория..."
    git init
    git branch -M main
fi

# Добавление remote origin
echo "🔗 Настройка remote origin..."
git remote remove origin 2>/dev/null || true
git remote add origin "$REPO_URL"

# Добавление всех файлов
echo "📁 Добавление файлов в Git..."
git add .

# Коммит
echo "💾 Создание коммита..."
git commit -m "🚀 Initial commit: SparkMatch Web App

✨ Features:
- Modern Telegram Web App interface
- Swipe gestures for dating profiles
- PWA support with service worker
- Responsive design for all devices
- Dark theme support
- Beautiful animations and effects

🎯 Ready for production deployment!"

# Отправка в GitHub
echo "⬆️ Отправка в GitHub..."
git push -u origin main

# Получение имени пользователя и репозитория из URL
REPO_NAME=$(echo "$REPO_URL" | sed 's/.*github\.com\/\([^\/]*\)\/\([^\/]*\)\.git.*/\2/')
USERNAME=$(echo "$REPO_URL" | sed 's/.*github\.com\/\([^\/]*\)\/\([^\/]*\)\.git.*/\1/')

# URL для GitHub Pages
PAGES_URL="https://${USERNAME}.github.io/${REPO_NAME}/"

echo ""
echo "🎉 Деплой завершен успешно!"
echo "=========================="
echo "📱 Ваш Web App доступен по адресу:"
echo "   $PAGES_URL"
echo ""
echo "⚙️ Следующие шаги:"
echo "1. Перейдите в BotFather: /mybots"
echo "2. Выберите вашего бота"
echo "3. Mini Apps → Menu Button → Set URL"
echo "4. Введите URL: $PAGES_URL"
echo "5. Сохраните настройки"
echo ""
echo "🔧 Для включения GitHub Pages:"
echo "1. Перейдите в Settings репозитория"
echo "2. Pages → Source: Deploy from a branch"
echo "3. Branch: main"
echo "4. Save"
echo ""
echo "✨ Готово! Ваш SparkMatch Web App готов к использованию!"

# Создание файла с инструкциями
cat > DEPLOYMENT_INFO.txt << EOF
🚀 SparkMatch Web App - Информация о деплое
===========================================

📱 Web App URL: $PAGES_URL
📅 Дата деплоя: $(date)
🔗 GitHub репозиторий: $REPO_URL

⚙️ Настройка в BotFather:
1. /mybots → выберите бота
2. Mini Apps → Menu Button → Set URL
3. Введите: $PAGES_URL
4. Сохраните

🔧 Включение GitHub Pages:
1. Settings репозитория
2. Pages → Source: Deploy from a branch
3. Branch: main
4. Save

📝 Тестирование:
1. Откройте бота в Telegram
2. Нажмите кнопку меню или Web App
3. Протестируйте все функции

✨ Готово к использованию!
EOF

echo "📄 Информация о деплое сохранена в DEPLOYMENT_INFO.txt"
