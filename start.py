#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт запуска Telegram Salon MVP
Автоматически запускает Backend и Telegram Bot
"""

import os
import sys
import subprocess
import platform
import time
from pathlib import Path

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

# Цвета для вывода (если поддерживается)
class Colors:
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    RESET = '\033[0m'
    
    @staticmethod
    def print_colored(text, color):
        """Вывод цветного текста (если терминал поддерживает)"""
        if platform.system() == 'Windows':
            # На Windows используем обычный вывод
            print(text)
        else:
            print(f"{color}{text}{Colors.RESET}")


def check_python():
    """Проверка версии Python"""
    if sys.version_info < (3, 8):
        Colors.print_colored("[ОШИБКА] Требуется Python 3.8 или выше", Colors.RED)
        Colors.print_colored(f"Текущая версия: {sys.version}", Colors.RED)
        return False
    Colors.print_colored(f"[OK] Python {sys.version.split()[0]}", Colors.GREEN)
    return True


def check_env_file():
    """Проверка наличия .env файла"""
    env_path = Path(".env")
    if not env_path.exists():
        Colors.print_colored("[ПРЕДУПРЕЖДЕНИЕ] Файл .env не найден!", Colors.YELLOW)
        Colors.print_colored("Создайте файл .env с содержимым:", Colors.YELLOW)
        print("BOT_TOKEN=your_bot_token_here")
        print("WEB_APP_URL=https://loguncov.github.io/telegram_salon_mvp/")
        print()
        return False
    return True


def setup_venv():
    """Создание и настройка виртуального окружения"""
    venv_path = Path("venv")
    
    if not venv_path.exists():
        Colors.print_colored("[ИНФО] Создание виртуального окружения...", Colors.YELLOW)
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
        Colors.print_colored("[OK] Виртуальное окружение создано", Colors.GREEN)
    
    # Определяем путь к pip в зависимости от ОС
    if platform.system() == 'Windows':
        pip_path = venv_path / "Scripts" / "pip.exe"
        python_path = venv_path / "Scripts" / "python.exe"
    else:
        pip_path = venv_path / "bin" / "pip"
        python_path = venv_path / "bin" / "python"
    
    return python_path, pip_path


def install_dependencies(pip_path):
    """Установка зависимостей"""
    Colors.print_colored("[ИНФО] Проверка зависимостей...", Colors.YELLOW)
    
    # Проверяем наличие fastapi
    result = subprocess.run(
        [str(pip_path), "show", "fastapi"],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        Colors.print_colored("[ИНФО] Установка зависимостей...", Colors.YELLOW)
        subprocess.run([str(pip_path), "install", "-r", "requirements.txt"], check=True)
        Colors.print_colored("[OK] Зависимости установлены", Colors.GREEN)
    else:
        Colors.print_colored("[OK] Зависимости уже установлены", Colors.GREEN)
    
    # Проверяем psutil после установки зависимостей
    global PSUTIL_AVAILABLE
    try:
        import psutil
        PSUTIL_AVAILABLE = True
    except ImportError:
        PSUTIL_AVAILABLE = False
        Colors.print_colored("[ПРЕДУПРЕЖДЕНИЕ] psutil не установлен, проверка процессов недоступна", Colors.YELLOW)


def check_process_running(process_name, script_name=None):
    """Проверка, запущен ли процесс"""
    if not PSUTIL_AVAILABLE:
        return False, None
    
    try:
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = proc.info.get('cmdline', [])
                if not cmdline:
                    continue
                
                cmdline_str = ' '.join(str(c) for c in cmdline)
                
                # Проверка по имени процесса и скрипта
                if process_name.lower() in proc.info.get('name', '').lower():
                    if script_name is None or script_name in cmdline_str:
                        return True, proc.info['pid']
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
    except Exception as e:
        Colors.print_colored(f"[ПРЕДУПРЕЖДЕНИЕ] Ошибка при проверке процессов: {e}", Colors.YELLOW)
    
    return False, None


def stop_process(pid):
    """Остановка процесса по PID"""
    if not PSUTIL_AVAILABLE:
        return False
    
    try:
        proc = psutil.Process(pid)
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except psutil.TimeoutExpired:
            proc.kill()
        return True
    except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
        Colors.print_colored(f"[ПРЕДУПРЕЖДЕНИЕ] Не удалось остановить процесс {pid}: {e}", Colors.YELLOW)
        return False


def start_backend(python_path):
    """Запуск Backend сервера"""
    Colors.print_colored("", Colors.RESET)
    Colors.print_colored("========================================", Colors.CYAN)
    Colors.print_colored("  Запуск Backend (порт 8000)", Colors.CYAN)
    Colors.print_colored("========================================", Colors.CYAN)
    
    # Проверка на запущенный backend
    is_running, pid = check_process_running("python", "uvicorn backend:app")
    if is_running:
        Colors.print_colored(f"[ПРЕДУПРЕЖДЕНИЕ] Backend уже запущен (PID: {pid})", Colors.YELLOW)
        response = input("Остановить существующий процесс и запустить новый? (y/n): ").strip().lower()
        if response == 'y':
            if stop_process(pid):
                Colors.print_colored("[OK] Старый процесс остановлен", Colors.GREEN)
                time.sleep(1)
            else:
                Colors.print_colored("[ОШИБКА] Не удалось остановить процесс", Colors.RED)
                return
        else:
            Colors.print_colored("[ИНФО] Используется существующий процесс", Colors.YELLOW)
            return
    
    if platform.system() == 'Windows':
        # Windows: запускаем в новом окне
        cmd = [
            "start", "cmd", "/k",
            f'"{python_path}" -m uvicorn backend:app --reload --host 0.0.0.0 --port 8000'
        ]
        subprocess.Popen(" ".join(cmd), shell=True)
    else:
        # Linux/Mac: запускаем в фоне
        cmd = [
            str(python_path), "-m", "uvicorn",
            "backend:app", "--reload", "--host", "0.0.0.0", "--port", "8000"
        ]
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    time.sleep(3)
    Colors.print_colored("[OK] Backend запущен", Colors.GREEN)


def start_bot(python_path):
    """Запуск Telegram Bot"""
    Colors.print_colored("", Colors.RESET)
    Colors.print_colored("========================================", Colors.CYAN)
    Colors.print_colored("  Запуск Telegram Bot", Colors.CYAN)
    Colors.print_colored("========================================", Colors.CYAN)
    
    # Проверка на запущенный бот
    is_running, pid = check_process_running("python", "bot.py")
    if is_running:
        Colors.print_colored(f"[ПРЕДУПРЕЖДЕНИЕ] Bot уже запущен (PID: {pid})", Colors.YELLOW)
        Colors.print_colored("Это может вызвать конфликт с Telegram API!", Colors.RED)
        response = input("Остановить существующий процесс и запустить новый? (y/n): ").strip().lower()
        if response == 'y':
            if stop_process(pid):
                Colors.print_colored("[OK] Старый процесс остановлен", Colors.GREEN)
                time.sleep(1)
            else:
                Colors.print_colored("[ОШИБКА] Не удалось остановить процесс", Colors.RED)
                Colors.print_colored("[ИНФО] Остановите процесс вручную перед запуском", Colors.YELLOW)
                return
        else:
            Colors.print_colored("[ОШИБКА] Нельзя запустить несколько экземпляров бота!", Colors.RED)
            Colors.print_colored("[ИНФО] Остановите существующий процесс перед запуском", Colors.YELLOW)
            return
    
    if platform.system() == 'Windows':
        # Windows: запускаем в новом окне
        cmd = [
            "start", "cmd", "/k",
            f'"{python_path}" bot.py'
        ]
        subprocess.Popen(" ".join(cmd), shell=True)
    else:
        # Linux/Mac: запускаем в фоне
        cmd = [str(python_path), "bot.py"]
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    Colors.print_colored("[OK] Bot запущен", Colors.GREEN)


def main():
    """Главная функция"""
    Colors.print_colored("========================================", Colors.CYAN)
    Colors.print_colored("  Telegram Salon MVP - Запуск проекта", Colors.CYAN)
    Colors.print_colored("========================================", Colors.CYAN)
    print()
    
    # Проверки
    if not check_python():
        sys.exit(1)
    
    check_env_file()
    
    # Настройка окружения
    python_path, pip_path = setup_venv()
    install_dependencies(pip_path)
    
    # Запуск сервисов
    start_backend(python_path)
    start_bot(python_path)
    
    # Итоговая информация
    print()
    Colors.print_colored("========================================", Colors.GREEN)
    Colors.print_colored("  Проект запущен!", Colors.GREEN)
    Colors.print_colored("========================================", Colors.GREEN)
    print()
    Colors.print_colored("Backend: http://localhost:8000", Colors.CYAN)
    Colors.print_colored("API Docs: http://localhost:8000/docs", Colors.CYAN)
    print()
    
    if platform.system() == 'Windows':
        Colors.print_colored("Окна с Backend и Bot открыты в отдельных окнах.", Colors.YELLOW)
        Colors.print_colored("Для остановки закройте эти окна или нажмите Ctrl+C.", Colors.YELLOW)
    else:
        Colors.print_colored("Backend и Bot запущены в фоновом режиме.", Colors.YELLOW)
        Colors.print_colored("Для остановки используйте: pkill -f 'uvicorn backend:app' и pkill -f 'bot.py'", Colors.YELLOW)
    
    print()
    input("Нажмите Enter для выхода...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[ИНФО] Завершение работы...")
        sys.exit(0)
    except Exception as e:
        Colors.print_colored(f"[ОШИБКА] {str(e)}", Colors.RED)
        sys.exit(1)

