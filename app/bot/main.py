from __future__ import annotations

import logging

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode

from app.bot.handlers import setup_router
from app.config import get_settings
from app.storage.repo import init_db

logger = logging.getLogger(__name__)


async def create_bot() -> Bot:
    settings = get_settings()
    return Bot(token=settings.telegram_bot_token, parse_mode=ParseMode.HTML)


async def create_dispatcher() -> Dispatcher:
    dispatcher = Dispatcher()
    dispatcher.include_router(setup_router())
    return dispatcher


async def on_startup(bot: Bot) -> None:
    await init_db()
    settings = get_settings()
    await bot.set_webhook(settings.webhook_url, drop_pending_updates=True)
    logger.info("Webhook set to %s", settings.webhook_url)


async def on_shutdown(bot: Bot) -> None:
    await bot.delete_webhook()
    logger.info("Webhook removed")

