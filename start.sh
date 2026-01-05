#!/bin/bash

echo "========================================"
echo "  Telegram Salon MVP - Запуск проекта"
echo "========================================"
echo ""

# Проверка наличия Python
if ! command -v python3 &> /dev/null; then
    echo "[ОШИБКА] Python3 не найден! Установите Python 3.8+"
    exit 1
fi

echo "[OK] Python найден: $(python3 --version)"

# Проверка наличия .env файла
if [ ! -f .env ]; then
    echo "[ПРЕДУПРЕЖДЕНИЕ] Файл .env не найден!"
    echo "Создайте файл .env с содержимым:"
    echo "BOT_TOKEN=your_bot_token_here"
    echo "WEB_APP_URL=https://loguncov.github.io/telegram_salon_mvp/"
    echo ""
fi

# Создание виртуального окружения если его нет
if [ ! -d "venv" ]; then
    echo "[ИНФО] Создание виртуального окружения..."
    python3 -m venv venv
fi

# Активация виртуального окружения
echo "[ИНФО] Активация виртуального окружения..."
source venv/bin/activate

# Проверка и установка зависимостей
if ! pip show fastapi &> /dev/null; then
    echo "[ИНФО] Установка зависимостей..."
    pip install -r requirements.txt
fi

echo ""
echo "========================================"
echo "  Запуск Backend (порт 8000)"
echo "========================================"

# Запуск Backend в фоне
python3 -m uvicorn backend:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

sleep 3

echo ""
echo "========================================"
echo "  Запуск Telegram Bot"
echo "========================================"

# Запуск Bot в фоне
python3 bot.py &
BOT_PID=$!

echo ""
echo "========================================"
echo "  Проект запущен!"
echo "========================================"
echo ""
echo "Backend: http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
echo ""
echo "Backend PID: $BACKEND_PID"
echo "Bot PID: $BOT_PID"
echo ""
echo "Для остановки нажмите Ctrl+C"
echo ""

# Ожидание сигнала завершения
trap "kill $BACKEND_PID $BOT_PID 2>/dev/null; exit" INT TERM
wait

