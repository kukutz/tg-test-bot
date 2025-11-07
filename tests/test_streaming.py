import pytest

from app.bot.utils.streaming import OpenAIStreamAggregator
from app.services.markdown import truncate_for_telegram


@pytest.mark.asyncio
async def test_streaming_emits_chunk(monkeypatch):
    aggregator = OpenAIStreamAggregator(min_edit_interval=0.0, chunk_char_limit=50)
    await aggregator.push("Hello <b>bold</b> world.")
    monkeypatch.setattr("app.bot.utils.streaming.time.monotonic", lambda: 1.0)
    update = await aggregator.build_update()
    assert update is not None
    assert "&lt;b&gt;" in update.payload.text
    assert not update.is_final


@pytest.mark.asyncio
async def test_streaming_finalize(monkeypatch):
    aggregator = OpenAIStreamAggregator(min_edit_interval=0.0)
    await aggregator.push("Sentence one. Sentence two.")
    final = await aggregator.finalize()
    assert final.is_final
    assert "Sentence two" in final.payload.text


def test_truncate_for_telegram():
    long_text = "A" * 5000
    rendered = truncate_for_telegram(long_text)
    assert rendered.truncated
    assert "См. полностью" in rendered.text

