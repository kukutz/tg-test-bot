from __future__ import annotations

import logging
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.types import Update
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from app.bot.main import create_bot, create_dispatcher, on_shutdown, on_startup
from app.config import get_settings
from app.services.markdown import markdown_to_html
from app.storage.repo import AnswerRepository, session_scope
from app.web.auth import verify_init_data

logger = logging.getLogger(__name__)

app = FastAPI(title="Telegram AI Assistant")

templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
app.mount(
    "/static",
    StaticFiles(directory=str(Path(__file__).parent / "static")),
    name="static",
)

_bot: Bot | None = None
dispatcher: Dispatcher | None = None


@app.on_event("startup")
async def startup_event() -> None:
    global _bot, dispatcher
    _bot = await create_bot()
    dispatcher = await create_dispatcher()
    await on_startup(_bot)
    logger.info("FastAPI application started")


@app.on_event("shutdown")
async def shutdown_event() -> None:
    if _bot is not None:
        await on_shutdown(_bot)
        await _bot.session.close()
    logger.info("FastAPI application stopped")


class RenderPayload(BaseModel):
    markdown: str


@app.get("/healthz")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/render")
async def render_endpoint(
    payload: RenderPayload,
    init_data: str = Header(default="", alias="X-Telegram-Init-Data"),
) -> dict[str, str]:
    verify_init_data(init_data)
    return {"html": markdown_to_html(payload.markdown)}


@app.get("/api/answers")
async def answers(
    mid: str,
    init_data: str = Header(default="", alias="X-Telegram-Init-Data"),
) -> dict[str, object]:
    verify_init_data(init_data)
    async with session_scope() as session:
        repo = AnswerRepository(session)
        answer = await repo.get_answer(mid)
        if not answer:
            raise HTTPException(status_code=404, detail="Answer not found")
        return {
            "markdown": answer.answer_md,
            "html": answer.answer_html,
            "meta": {
                "model": answer.model,
                "created_at": answer.created_at.isoformat(),
                "mode": answer.mode,
            },
        }


@app.post("/webhook")
async def telegram_webhook(request: Request) -> JSONResponse:
    if _bot is None or dispatcher is None:
        raise HTTPException(status_code=503, detail="Bot not ready")
    data = await request.json()
    update = Update.model_validate(data)
    await dispatcher.feed_update(_bot, update)
    return JSONResponse({"ok": True})


@app.get("/view", response_class=HTMLResponse)
async def view_page(request: Request, mid: str | None = None) -> HTMLResponse:
    settings = get_settings()
    return templates.TemplateResponse(
        "webapp.html",
        {
            "request": request,
            "mode": "view",
            "answer_id": mid,
            "bot_username": (
                settings.telegram_bot_username
                or settings.telegram_bot_token.split(":")[0]
            ),
        },
    )


@app.get("/inline", response_class=HTMLResponse)
async def inline_page(request: Request) -> HTMLResponse:
    settings = get_settings()
    return templates.TemplateResponse(
        "webapp.html",
        {
            "request": request,
            "mode": "inline",
            "answer_id": None,
            "bot_username": (
                settings.telegram_bot_username
                or settings.telegram_bot_token.split(":")[0]
            ),
        },
    )

