from __future__ import annotations

import logging

from aiogram import Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import ErrorEvent

router = Router()
logger = logging.getLogger(__name__)


@router.errors()
async def log_errors(event: ErrorEvent) -> None:
    if isinstance(event.exception, TelegramBadRequest) and "message is not modified" in str(
        event.exception,
    ).lower():
        return
    logger.exception("Unhandled bot error", exc_info=event.exception)

