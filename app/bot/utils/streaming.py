from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass

from app.services.markdown import RenderedMessage, render_for_telegram, truncate_for_telegram


@dataclass(slots=True)
class StreamUpdate:
    payload: RenderedMessage
    is_final: bool


class OpenAIStreamAggregator:
    """Collects streamed deltas and produces throttled Telegram-ready updates."""

    def __init__(
        self,
        min_edit_interval: float = 1.0,
        chunk_char_limit: int = 480,
        max_message_length: int = 3900,
    ) -> None:
        self._min_edit_interval = min_edit_interval
        self._chunk_char_limit = chunk_char_limit
        self._max_message_length = max_message_length
        self._full_text: list[str] = []
        self._sent_index = 0
        self._last_emit = 0.0
        self._truncated = False
        self._lock = asyncio.Lock()

    async def push(self, delta: str) -> None:
        async with self._lock:
            self._full_text.append(delta)

    async def build_update(self) -> StreamUpdate | None:
        async with self._lock:
            now = time.monotonic()
            if self._truncated:
                return None
            if now - self._last_emit < self._min_edit_interval:
                return None
            consumed = self._consume_chunk()
            if consumed is None:
                return None
            text = "".join(self._full_text)[: self._sent_index]
            html_message = render_for_telegram(text)
            rendered = truncate_for_telegram(html_message, self._max_message_length)
            if rendered.truncated:
                self._truncated = True
            self._last_emit = now
            return StreamUpdate(payload=rendered, is_final=False)

    async def finalize(self) -> StreamUpdate:
        async with self._lock:
            text = "".join(self._full_text)
            self._sent_index = len(text)
            html_message = render_for_telegram(text)
            rendered = truncate_for_telegram(html_message, self._max_message_length)
            if rendered.truncated:
                self._truncated = True
            return StreamUpdate(payload=rendered, is_final=True)

    async def get_full_text(self) -> str:
        async with self._lock:
            return "".join(self._full_text)

    def _consume_chunk(self) -> str | None:
        full_text = "".join(self._full_text)
        if self._sent_index >= len(full_text):
            return None
        remaining = full_text[self._sent_index :]
        if not remaining.strip():
            return None
        boundary = self._find_boundary(remaining)
        if boundary == 0:
            return None
        self._sent_index += boundary
        return remaining[:boundary]

    def _find_boundary(self, text: str) -> int:
        limit = min(len(text), self._chunk_char_limit)
        preferred_delimiters = [". ", "!", "?", "\n"]
        slice_text = text[:limit]
        best = -1
        for delimiter in preferred_delimiters:
            idx = slice_text.rfind(delimiter)
            if idx > best:
                best = idx + (len(delimiter) if idx != -1 else 0)
        if best <= 0 and len(text) > limit:
            return limit
        if best <= 0:
            return len(text)
        return best


async def drain_stream(
    aggregator: OpenAIStreamAggregator,
    sse_iterator: asyncio.AsyncIterator[str],
    on_update: callable[[StreamUpdate], asyncio.Future | asyncio.Task | None],
) -> StreamUpdate:
    async for delta in sse_iterator:
        await aggregator.push(delta)
        update = await aggregator.build_update()
        if update:
            task = on_update(update)
            if task is not None:
                await asyncio.shield(task)
    final_update = await aggregator.finalize()
    task = on_update(final_update)
    if task is not None:
        await asyncio.shield(task)
    return final_update

