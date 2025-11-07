from __future__ import annotations

import argparse
import asyncio
import logging

import uvicorn

from app.bot.main import create_bot, create_dispatcher
from app.storage.repo import init_db

logging.basicConfig(level=logging.INFO)


async def run_bot_polling() -> None:
    await init_db()
    bot = await create_bot()
    dispatcher = await create_dispatcher()
    try:
        await dispatcher.start_polling(bot)
    finally:
        await bot.session.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Telegram AI Assistant")
    parser.add_argument("mode", choices=["bot", "web"], help="Запуск бота или веб-сервера")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    if args.mode == "bot":
        asyncio.run(run_bot_polling())
    elif args.mode == "web":
        uvicorn.run("app.web.main:app", host=args.host, port=args.port, reload=False)


if __name__ == "__main__":
    main()

