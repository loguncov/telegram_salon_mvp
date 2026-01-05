@echo off
chcp 65001 >nul
echo ========================================
echo   Telegram Salon MVP - Запуск проекта
echo ========================================
echo.

REM Проверка наличия Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ОШИБКА] Python не найден! Установите Python 3.8+
    pause
    exit /b 1
)

REM Проверка наличия .env файла
if not exist .env (
    echo [ПРЕДУПРЕЖДЕНИЕ] Файл .env не найден!
    echo Создайте файл .env с содержимым:
    echo BOT_TOKEN=your_bot_token_here
    echo WEB_APP_URL=https://loguncov.github.io/telegram_salon_mvp/
    echo.
    pause
)

REM Проверка установки зависимостей
if not exist venv (
    echo [ИНФО] Создание виртуального окружения...
    python -m venv venv
)

echo [ИНФО] Активация виртуального окружения...
call venv\Scripts\activate.bat

echo [ИНФО] Проверка зависимостей...
pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo [ИНФО] Установка зависимостей...
    pip install -r requirements.txt
)

echo.
echo ========================================
echo   Запуск Backend (порт 8000)
echo ========================================
start "Telegram Salon - Backend" cmd /k "venv\Scripts\activate.bat && python -m uvicorn backend:app --reload --host 0.0.0.0 --port 8000"

timeout /t 3 /nobreak >nul

echo.
echo ========================================
echo   Запуск Telegram Bot
echo ========================================
start "Telegram Salon - Bot" cmd /k "venv\Scripts\activate.bat && python bot.py"

echo.
echo ========================================
echo   Проект запущен!
echo ========================================
echo.
echo Backend: http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo.
echo Окна с Backend и Bot открыты в отдельных окнах.
echo Для остановки закройте эти окна или нажмите Ctrl+C.
echo.
pause

