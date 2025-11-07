from __future__ import annotations

from aiogram import Router

from . import errors, inline, message


def setup_router() -> Router:
    router = Router()
    router.include_router(message.router)
    router.include_router(inline.router)
    router.include_router(errors.router)
    return router

