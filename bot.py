import asyncio
import os
import json
from aiogram import Bot, Dispatcher
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from dotenv import load_dotenv

# #region agent log
def debug_log(location, message, data=None, hypothesis_id=None):
    try:
        with open('.cursor/debug.log', 'a', encoding='utf-8') as f:
            f.write(json.dumps({
                'location': location,
                'message': message,
                'data': data or {},
                'timestamp': int(asyncio.get_event_loop().time() * 1000) if hasattr(asyncio, 'get_event_loop') else 0,
                'sessionId': 'debug-session',
                'runId': 'run1',
                'hypothesisId': hypothesis_id
            }, ensure_ascii=False) + '\n')
    except: pass
# #endregion

load_dotenv()
debug_log('bot.py:18', 'load_dotenv called', {}, 'A')

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEB_APP_URL = os.getenv("WEB_APP_URL", "https://loguncov.github.io/telegram_salon_mvp/")
debug_log('bot.py:22', 'Environment variables loaded', {'has_token': bool(BOT_TOKEN), 'web_app_url': WEB_APP_URL}, 'A')

# Telegram требует HTTPS для Web App
if WEB_APP_URL and not WEB_APP_URL.startswith("https://"):
    print(f"[WARN] WEB_APP_URL должен быть HTTPS. Текущий: {WEB_APP_URL}")
    print(f"[WARN] Используется дефолтный URL: https://loguncov.github.io/telegram_salon_mvp/")
    WEB_APP_URL = "https://loguncov.github.io/telegram_salon_mvp/"
    debug_log('bot.py:28', 'WEB_APP_URL changed to HTTPS', {'new_url': WEB_APP_URL}, 'C')

debug_log('bot.py:30', 'Before BOT_TOKEN check', {'has_token': bool(BOT_TOKEN)}, 'A')
if not BOT_TOKEN:
    debug_log('bot.py:32', 'BOT_TOKEN missing - raising error', {}, 'A')
    raise RuntimeError("BOT_TOKEN not set in .env file")

print(f"[OK] BOT_TOKEN загружен")
print(f"[OK] WEB_APP_URL: {WEB_APP_URL}")

debug_log('bot.py:37', 'Before Bot initialization', {'web_app_url': WEB_APP_URL}, 'E')
try:
    bot = Bot(BOT_TOKEN)
    debug_log('bot.py:40', 'Bot initialized successfully', {}, 'E')
except Exception as e:
    debug_log('bot.py:42', 'Bot initialization failed', {'error': str(e)}, 'E')
    raise

dp = Dispatcher()
debug_log('bot.py:45', 'Dispatcher created', {}, 'E')

print("[OK] Бот инициализирован, запуск polling...")

@dp.message(Command("start"))
async def start(message: Message):
    debug_log('bot.py:50', 'start command received', {'user_id': message.from_user.id if message.from_user else None}, 'E')
    try:
        debug_log('bot.py:52', 'Creating keyboard', {'web_app_url': WEB_APP_URL}, 'C')
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="💅 Открыть приложение",
                web_app={"url": WEB_APP_URL}
            )]
        ])
        debug_log('bot.py:59', 'Keyboard created, sending message', {}, 'E')
        await message.answer("Открой приложение салона:", reply_markup=kb)
        debug_log('bot.py:61', 'Message sent successfully', {}, 'E')
    except Exception as e:
        debug_log('bot.py:63', 'Error in start handler', {'error': str(e), 'error_type': type(e).__name__}, 'D')
        print(f"[ERROR] Ошибка при отправке сообщения: {e}")
        await message.answer(
            f"Ошибка: {str(e)}\n\n"
            f"Проверьте WEB_APP_URL в .env файле. "
            f"Должен быть HTTPS URL (например: https://loguncov.github.io/telegram_salon_mvp/)"
        )

async def main():
    debug_log('bot.py:71', 'Starting polling', {}, 'E')
    try:
        await dp.start_polling(bot)
        debug_log('bot.py:73', 'Polling started successfully', {}, 'E')
    except Exception as e:
        debug_log('bot.py:75', 'Polling failed', {'error': str(e), 'error_type': type(e).__name__}, 'B')
        raise

if __name__ == "__main__":
    debug_log('bot.py:78', 'Script started', {}, 'B')
    asyncio.run(main())
