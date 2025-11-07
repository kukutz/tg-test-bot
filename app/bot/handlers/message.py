from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

from aiogram import Router, types
from aiogram.enums import ChatAction
from aiogram.exceptions import TelegramBadRequest, TelegramRetryAfter
from aiogram.filters import Command

from app.bot.keyboards.common import answer_keyboard, start_keyboard
from app.bot.utils.streaming import OpenAIStreamAggregator, StreamUpdate, drain_stream
from app.config import get_settings
from app.services.openai_client import resilient_stream
from app.storage.repo import AnswerRepository, session_scope

router = Router()


@router.message(Command("start"))
async def cmd_start(message: types.Message) -> None:
    settings = get_settings()
    text = (
        "Привет! Я бот-помощник с тремя режимами:\n\n"
        "• Обычный чат — напиши запрос, и я отвечу стримингом.\n"
        "• Инлайн — попробуй в любом чате: @%s <вопрос>.\n"
        "• Мини-апп — сохраню полный ответ и красиво его покажу." % (
            settings.telegram_bot_username or "bot"
        )
    )
    await message.answer(
        text,
        reply_markup=start_keyboard(),
        input_field_placeholder="Спроси что-нибудь...",
    )


async def _edit_with_backoff(message: types.Message, text: str) -> None:
    delay = 1.0
    while True:
        try:
            await message.edit_text(text, parse_mode="HTML")
            break
        except TelegramRetryAfter as exc:
            await asyncio.sleep(exc.retry_after)
        except TelegramBadRequest as exc:
            if "message is not modified" in exc.message.lower():
                break
            await asyncio.sleep(delay)
            delay = min(delay * 2, 8.0)


@router.message()
async def handle_text(message: types.Message) -> None:
    if not message.text:
        return
    await message.answer_chat_action(ChatAction.TYPING)
    status = await message.reply("Генерирую…")
    aggregator = OpenAIStreamAggregator()

    async def sse_iterator() -> AsyncIterator[str]:
        async for chunk in resilient_stream(
            [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": message.text},
            ],
        ):
            yield chunk

    async def on_update(update: StreamUpdate) -> None:
        await _edit_with_backoff(status, update.payload.text)

    try:
        await drain_stream(aggregator, sse_iterator(), on_update)
        full_text = await aggregator.get_full_text()
        settings = get_settings()
        async with session_scope() as session:
            repo = AnswerRepository(session)
            answer = await repo.create_answer(
                chat_id=str(message.chat.id),
                message_id=status.message_id,
                inline_query_id=None,
                mode="chat",
                prompt=message.text,
                answer_md=full_text,
                model=settings.openai_model,
            )
        await status.edit_reply_markup(reply_markup=answer_keyboard(answer.id))
    except Exception:
        await status.edit_text("Произошла ошибка. Попробуйте позже.")
        raise

