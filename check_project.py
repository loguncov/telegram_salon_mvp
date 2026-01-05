"""
Скрипт для проверки работоспособности проекта
"""
import httpx
import sys
import time

BASE_URL = "http://localhost:8000"
TEST_USER_ID = "test_user_123"

def check_backend():
    """Проверка работоспособности backend"""
    print("[*] Проверка backend...")
    
    try:
        # Health check
        response = httpx.get(f"{BASE_URL}/health", timeout=2)
        if response.status_code == 200:
            print("[OK] Health check: OK")
        else:
            print(f"[ERROR] Health check: {response.status_code}")
            return False
        
        # Проверка API документации
        response = httpx.get(f"{BASE_URL}/docs", timeout=2)
        if response.status_code == 200:
            print("[OK] API документация доступна: http://localhost:8000/docs")
        else:
            print(f"[WARN] API документация: {response.status_code}")
        
        # Проверка списка салонов (публичный endpoint)
        response = httpx.get(f"{BASE_URL}/api/client/salons", timeout=2)
        if response.status_code == 200:
            data = response.json()
            print(f"[OK] API клиентов работает: найдено салонов - {len(data.get('items', []))}")
        else:
            print(f"[ERROR] API клиентов: {response.status_code}")
            return False
        
        # Проверка создания салона
        response = httpx.post(
            f"{BASE_URL}/api/owner/salon",
            json={"name": "Тестовый салон"},
            headers={"X-User-Id": TEST_USER_ID},
            timeout=2
        )
        if response.status_code == 200:
            salon = response.json()
            print(f"[OK] Создание салона: OK (ID: {salon['id'][:8]}...)")
            
            # Проверка получения салона
            response = httpx.get(
                f"{BASE_URL}/api/owner/salon",
                headers={"X-User-Id": TEST_USER_ID},
                timeout=2
            )
            if response.status_code == 200:
                print("[OK] Получение салона: OK")
            
            # Проверка добавления мастера
            response = httpx.post(
                f"{BASE_URL}/api/owner/masters",
                json={"name": "Test Master", "telegram_id": "99999"},
                headers={"X-User-Id": TEST_USER_ID},
                timeout=2
            )
            if response.status_code == 200:
                print("[OK] Добавление мастера: OK")
            
            # Проверка добавления услуги
            response = httpx.post(
                f"{BASE_URL}/api/owner/services",
                json={"name": "Test Service"},
                headers={"X-User-Id": TEST_USER_ID},
                timeout=2
            )
            if response.status_code == 200:
                print("[OK] Добавление услуги: OK")
            
            # Проверка определения роли
            response = httpx.get(
                f"{BASE_URL}/api/user/role",
                headers={"X-User-Id": TEST_USER_ID},
                timeout=2
            )
            if response.status_code == 200:
                role_data = response.json()
                print(f"[OK] Определение роли: {role_data['role']}")
            
        else:
            print(f"[WARN] Создание салона: {response.status_code} (возможно, салон уже существует)")
        
        # Проверка главной страницы
        response = httpx.get(f"{BASE_URL}/", timeout=2)
        if response.status_code == 200:
            if "Salon WebApp" in response.text or "telegram-web-app" in response.text.lower():
                print("[OK] Web App доступен: http://localhost:8000/")
            else:
                print("[WARN] Главная страница загружается, но содержимое неожиданное")
        else:
            print(f"[WARN] Главная страница: {response.status_code}")
        
        return True
        
    except (httpx.ConnectError, httpx.ConnectTimeout):
        print("[ERROR] Backend не запущен! Запустите: python -m uvicorn backend:app --reload")
        return False
    except Exception as e:
        print(f"[ERROR] Ошибка при проверке: {e}")
        return False

def main():
    print("=" * 50)
    print("Проверка проекта Telegram Salon MVP")
    print("=" * 50)
    print()
    
    # Небольшая задержка для инициализации
    time.sleep(1)
    
    if check_backend():
        print()
        print("=" * 50)
        print("[SUCCESS] Backend работает корректно!")
        print("=" * 50)
        print()
        print("Следующие шаги:")
        print("1. Откройте http://localhost:8000/docs для просмотра API")
        print("2. Откройте http://localhost:8000/ для Web App")
        print("3. Для запуска бота создайте .env файл с BOT_TOKEN")
        print("4. Запустите бота: python bot.py")
        print()
        return 0
    else:
        print()
        print("=" * 50)
        print("[ERROR] Обнаружены проблемы!")
        print("=" * 50)
        return 1

if __name__ == "__main__":
    sys.exit(main())

