# Changelog

## 2026-01-05
- Added unified `run.py` entrypoint that starts FastAPI and the aiogram bot together with graceful shutdown.
- Introduced env-driven configuration (`.env.example`, `config.py`) and SQLite auto-init with seed data.
- Enabled static serving and CORS tweaks, improved `/health` with timestamp and added smoke test `tests/test_health.py`.
- Updated WebApp to work from local origin/Telegram, added health badge and relative `/api` calls.
- Refreshed README with new setup/run instructions and verification steps.

