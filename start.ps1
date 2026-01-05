# Telegram Salon MVP - PowerShell скрипт запуска

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Telegram Salon MVP - Запуск проекта" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Проверка наличия Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "[OK] $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "[ОШИБКА] Python не найден! Установите Python 3.8+" -ForegroundColor Red
    Read-Host "Нажмите Enter для выхода"
    exit 1
}

# Проверка наличия .env файла
if (-not (Test-Path ".env")) {
    Write-Host "[ПРЕДУПРЕЖДЕНИЕ] Файл .env не найден!" -ForegroundColor Yellow
    Write-Host "Создайте файл .env с содержимым:" -ForegroundColor Yellow
    Write-Host "BOT_TOKEN=your_bot_token_here" -ForegroundColor Yellow
    Write-Host "WEB_APP_URL=https://loguncov.github.io/telegram_salon_mvp/" -ForegroundColor Yellow
    Write-Host ""
}

# Создание виртуального окружения если его нет
if (-not (Test-Path "venv")) {
    Write-Host "[ИНФО] Создание виртуального окружения..." -ForegroundColor Yellow
    python -m venv venv
}

# Активация виртуального окружения
Write-Host "[ИНФО] Активация виртуального окружения..." -ForegroundColor Yellow
& "venv\Scripts\Activate.ps1"

# Проверка и установка зависимостей
$fastapiInstalled = pip show fastapi 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ИНФО] Установка зависимостей..." -ForegroundColor Yellow
    pip install -r requirements.txt
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Запуск Backend (порт 8000)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Запуск Backend в новом окне
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$PWD'; venv\Scripts\Activate.ps1; python -m uvicorn backend:app --reload --host 0.0.0.0 --port 8000"
) -WindowStyle Normal

Start-Sleep -Seconds 3

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Запуск Telegram Bot" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Запуск Bot в новом окне
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$PWD'; venv\Scripts\Activate.ps1; python bot.py"
) -WindowStyle Normal

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Проект запущен!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Backend: http://localhost:8000" -ForegroundColor Cyan
Write-Host "API Docs: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "Окна с Backend и Bot открыты в отдельных окнах." -ForegroundColor Yellow
Write-Host "Для остановки закройте эти окна или нажмите Ctrl+C." -ForegroundColor Yellow
Write-Host ""
Read-Host "Нажмите Enter для выхода"

