"""Unified entrypoint to run FastAPI backend and Telegram bot together."""
from __future__ import annotations

import asyncio
import contextlib
import logging

import uvicorn

from backend import app
from bot import start_bot, shutdown_bot
from config import get_settings
from database import init_db


logger = logging.getLogger(__name__)


async def main():
    settings = get_settings()

    logging.basicConfig(
        level=logging.DEBUG if settings.debug else logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )
    logger.info("Starting services on %s:%s", settings.host, settings.port)

    # Ensure DB schema exists before serving requests
    init_db()

    server_config = uvicorn.Config(
        app,
        host=settings.host,
        port=settings.port,
        log_level="debug" if settings.debug else "info",
        reload=False,
    )
    server = uvicorn.Server(server_config)

    api_task = asyncio.create_task(server.serve(), name="api-server")
    bot_task = asyncio.create_task(start_bot(), name="telegram-bot")
    tasks = {api_task, bot_task}

    try:
        done, pending = await asyncio.wait(
            tasks, return_when=asyncio.FIRST_EXCEPTION
        )
        for task in done:
            if task.cancelled():
                continue
            if task.exception():
                logger.error(
                    "Task %s failed: %s", task.get_name(), task.exception()
                )
                for pending_task in pending:
                    pending_task.cancel()
    except asyncio.CancelledError:
        logger.info("Shutdown requested (CancelledError)")
    finally:
        logger.info("Stopping services...")
        server.should_exit = True
        for task in tasks:
            task.cancel()

        with contextlib.suppress(Exception):
            await shutdown_bot()
        with contextlib.suppress(Exception):
            await api_task
        with contextlib.suppress(Exception):
            await bot_task

        logger.info("Shutdown complete")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Interrupted by user")

