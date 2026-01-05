# Telegram Salon MVP

Telegram WebApp + FastAPI backend + aiogram bot for a beauty salon MVP.

## Requirements
- Python 3.10+
- (optional) ngrok/Cloudflare Tunnel for testing WebApp via HTTPS in Telegram

## Setup
`ash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
# Р·Р°РїРѕР»РЅРёС‚Рµ BOT_TOKEN, РїСЂРё РЅРµРѕР±С…РѕРґРёРјРѕСЃС‚Рё WEB_APP_URL
`

### Environment variables
- BOT_TOKEN вЂ” Telegram Bot API С‚РѕРєРµРЅ (РѕР±СЏР·Р°С‚РµР»СЊРЅРѕ)
- WEB_APP_URL вЂ” URL, РєРѕС‚РѕСЂС‹Р№ РѕС‚РєСЂС‹РІР°РµС‚ Р±РѕС‚ (РїРѕ СѓРјРѕР»С‡Р°РЅРёСЋ http://localhost:8000)
- DATABASE_URL вЂ” sqlite:///./salon.db РїРѕ СѓРјРѕР»С‡Р°РЅРёСЋ
- HOST / PORT вЂ” РєСѓРґР° РїРѕРґРЅРёРјР°С‚СЊ backend (РїРѕ СѓРјРѕР»С‡Р°РЅРёСЋ 127.0.0.1:8000)
- APP_DEBUG вЂ” 	rue/false СѓСЂРѕРІРµРЅСЊ Р»РѕРіРёСЂРѕРІР°РЅРёСЏ

## Run (single entrypoint)
`ash
python run.py
`
- РџРѕРґРЅРёРјР°РµС‚ FastAPI РЅР° HOST:PORT
- РЎС‚Р°СЂС‚СѓРµС‚ aiogram polling РІ РїР°СЂР°Р»Р»РµР»СЊРЅРѕР№ Р·Р°РґР°С‡Рµ
- РђРІС‚РѕРјР°С‚РёС‡РµСЃРєРё РёРЅРёС†РёР°Р»РёР·РёСЂСѓРµС‚ SQLite Рё С‚РµСЃС‚РѕРІС‹Рµ РґР°РЅРЅС‹Рµ (РѕРґРёРЅ СЃР°Р»РѕРЅ/РјР°СЃС‚РµСЂ/СѓСЃР»СѓРіР°)

## Health check / smoke test
`ash
curl http://127.0.0.1:8000/health
# в†’ {"status":"ok","time":"2026-01-05T12:00:00Z"}
`
- РћС‚РєСЂРѕР№С‚Рµ http://127.0.0.1:8000 РІ Р±СЂР°СѓР·РµСЂРµ вЂ” Р·Р°РіСЂСѓР·РёС‚СЃСЏ Р»РѕРєР°Р»СЊРЅС‹Р№ WebApp
- Р’СЃРµ Р·Р°РїСЂРѕСЃС‹ СЃ С„СЂРѕРЅС‚Р° РёРґСѓС‚ РЅР° РѕС‚РЅРѕСЃРёС‚РµР»СЊРЅС‹Р№ /api/..., CORS РЅР°СЃС‚СЂРѕРµРЅ РїРѕРґ РІР°С€ WEB_APP_URL

## Telegram WebApp tips
- Р’ WEB_APP_URL СѓРєР°Р¶РёС‚Рµ РїСѓР±Р»РёС‡РЅС‹Р№ URL (https) РёР· С‚СѓРЅРЅРµР»СЏ, РЅР°РїСЂРёРјРµСЂ https://<id>.ngrok.io
- Р’ Р±РѕС‚Рµ /start в†’ РєРЅРѕРїРєР° В«рџ’… РћС‚РєСЂС‹С‚СЊ РїСЂРёР»РѕР¶РµРЅРёРµВ» РѕС‚РєСЂРѕРµС‚ WebApp РїРѕ WEB_APP_URL
- Р¤РѕР»Р±СЌРє РґР»СЏ Р»РѕРєР°Р»СЊРЅРѕР№ РѕС‚Р»Р°РґРєРё: РµСЃР»Рё РѕС‚РєСЂС‹С‚СЊ РІ Р±СЂР°СѓР·РµСЂРµ, РёСЃРїРѕР»СЊР·СѓРµС‚СЃСЏ С‚РµСЃС‚РѕРІС‹Р№ user-id local-user

## Tests
`ash
pytest -q
`
- Р’РєР»СЋС‡Р°РµС‚ Р±С‹СЃС‚СЂС‹Р№ С‚РµСЃС‚ 	ests/test_health.py

## Project structure
`
telegram_salon_mvp/
в”њв”Ђв”Ђ run.py             # РµРґРёРЅС‹Р№ entrypoint (FastAPI + bot)
в”њв”Ђв”Ђ backend.py         # FastAPI РїСЂРёР»РѕР¶РµРЅРёРµ (/api + /health + СЃС‚Р°С‚РёРєР°)
в”њв”Ђв”Ђ bot.py             # aiogram v3 Р±РѕС‚, webapp РєРЅРѕРїРєР°
в”њв”Ђв”Ђ database.py        # SQLite, init + seed
в”њв”Ђв”Ђ index.html         # WebApp (Telegram/Р±СЂР°СѓР·РµСЂ)
в”њв”Ђв”Ђ tests/test_health.py
в”њв”Ђв”Ђ requirements.txt
в””в”Ђв”Ђ README.md
`

## Manual verification checklist
1) python run.py
2) curl http://127.0.0.1:8000/health в†’ {"status":"ok", ...}
3) РћС‚РєСЂС‹С‚СЊ http://127.0.0.1:8000 РІ Р±СЂР°СѓР·РµСЂРµ в†’ WebApp РіСЂСѓР·РёС‚СЃСЏ, health В«Backend РґРѕСЃС‚СѓРїРµРЅВ»
4) Р’ Telegram: /start в†’ РєРЅРѕРїРєР° РѕС‚РєСЂРѕРµС‚ WebApp РїРѕ WEB_APP_URL, Р·Р°РїСЂРѕСЃС‹ РёРґСѓС‚ РЅР° РІР°С€ backend

## Changelog
РЎРј. CHANGELOG.md РґР»СЏ РєСЂР°С‚РєРѕРіРѕ РїРµСЂРµС‡РЅСЏ РёР·РјРµРЅРµРЅРёР№.
