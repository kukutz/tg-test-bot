from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

from aiogram import Bot, Router, types
from aiogram.exceptions import TelegramBadRequest, TelegramRetryAfter

from app.bot.keyboards.common import inline_answer_keyboard, inline_suggestions_keyboard
from app.bot.utils.streaming import OpenAIStreamAggregator, StreamUpdate, drain_stream
from app.config import get_settings
from app.services.openai_client import resilient_stream
from app.storage.repo import AnswerRepository, session_scope

router = Router()


@router.inline_query()
async def inline_query_handler(query: types.InlineQuery) -> None:
    user_query = query.query.strip()
    if not user_query:
        user_query = "Сформулируйте запрос"
    description = f"{user_query[:64]}" if user_query else "Введите текст"
    results = [
        types.InlineQueryResultArticle(
            id="text",
            title="Написать ответ",
            description=description,
            input_message_content=types.InputTextMessageContent(
                message_text="Генерирую…",
                parse_mode="HTML",
            ),
            reply_markup=inline_suggestions_keyboard(),
        ),
        types.InlineQueryResultArticle(
            id="image",
            title="Сгенерировать картинку",
            description=description,
            input_message_content=types.InputTextMessageContent(
                message_text="Сорри, пока не готово",
            ),
            reply_markup=inline_suggestions_keyboard(),
        ),
    ]
    await query.answer(results=results, cache_time=0, is_personal=True)


async def _edit_inline(bot: Bot, inline_message_id: str, text: str) -> None:
    delay = 1.0
    while True:
        try:
            await bot.edit_message_text(
                inline_message_id=inline_message_id,
                text=text,
                parse_mode="HTML",
            )
            break
        except TelegramRetryAfter as exc:
            await asyncio.sleep(exc.retry_after)
        except TelegramBadRequest as exc:
            if "message is not modified" in exc.message.lower():
                break
            await asyncio.sleep(delay)
            delay = min(delay * 2, 8.0)


@router.chosen_inline_result()
async def chosen_inline(result: types.ChosenInlineResult, bot: Bot) -> None:
    if result.result_id != "text" or not result.inline_message_id:
        return
    prompt = result.query
    if not prompt:
        await _edit_inline(bot, result.inline_message_id, "Нужен текст запроса")
        return
    aggregator = OpenAIStreamAggregator()

    async def sse_iterator() -> AsyncIterator[str]:
        async for chunk in resilient_stream(
            [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt},
            ],
        ):
            yield chunk

    async def on_update(update: StreamUpdate) -> None:
        await _edit_inline(bot, result.inline_message_id, update.payload.text)

    settings = get_settings()
    try:
        await drain_stream(aggregator, sse_iterator(), on_update)
        full_text = await aggregator.get_full_text()
        async with session_scope() as session:
            repo = AnswerRepository(session)
            answer = await repo.create_answer(
                chat_id=None,
                message_id=None,
                inline_query_id=result.inline_message_id,
                mode="inline",
                prompt=prompt,
                answer_md=full_text,
                model=settings.openai_model,
            )
        keyboard = inline_answer_keyboard(answer.id)
        await bot.edit_message_reply_markup(
            inline_message_id=result.inline_message_id,
            reply_markup=keyboard,
        )
    except Exception:
        await _edit_inline(bot, result.inline_message_id, "Не удалось сгенерировать ответ")
        raise

