from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncGenerator, Iterable

import httpx

from app.config import get_settings


class OpenAIError(RuntimeError):
    pass


class OpenAIClient:
    def __init__(self) -> None:
        self._settings = get_settings()
        self._client = httpx.AsyncClient(
            base_url="https://api.openai.com/v1",
            headers={
                "Authorization": f"Bearer {self._settings.openai_api_key}",
                "Content-Type": "application/json",
            },
            timeout=httpx.Timeout(60.0, read=None),
        )

    async def stream_chat_completion(
        self,
        messages: Iterable[dict[str, str]],
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> AsyncGenerator[str, None]:
        payload = {
            "model": self._settings.openai_model,
            "messages": list(messages),
            "stream": True,
        }
        if temperature is not None:
            payload["temperature"] = temperature
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        async with self._client.stream("POST", "/chat/completions", json=payload) as response:
            if response.status_code >= 400:
                text = await response.aread()
                raise OpenAIError(text.decode())
            async for line in response.aiter_lines():
                if not line:
                    continue
                if line.startswith("data: "):
                    data = line.removeprefix("data: ").strip()
                    if data == "[DONE]":
                        break
                    chunk = json.loads(data)
                    delta = chunk["choices"][0]["delta"].get("content")
                    if delta:
                        yield delta

    async def generate_image(self, prompt: str, size: str = "1024x1024") -> dict[str, str]:
        payload = {
            "model": "gpt-image-1",
            "prompt": prompt,
            "size": size,
        }
        response = await self._client.post("/images/generations", json=payload)
        if response.status_code >= 400:
            raise OpenAIError(response.text)
        result = response.json()
        return result["data"][0]

    async def close(self) -> None:
        await self._client.aclose()


async def stream_chat(messages: Iterable[dict[str, str]]) -> AsyncGenerator[str, None]:
    client = OpenAIClient()
    try:
        async for chunk in client.stream_chat_completion(messages):
            yield chunk
    finally:
        await client.close()


async def resilient_stream(
    messages: Iterable[dict[str, str]],
    *,
    retries: int = 3,
    base_delay: float = 1.0,
) -> AsyncGenerator[str, None]:
    attempt = 0
    while True:
        try:
            async for chunk in stream_chat(messages):
                yield chunk
            break
        except OpenAIError:
            if attempt >= retries:
                raise
            await asyncio.sleep(base_delay * (2 ** attempt))
            attempt += 1

