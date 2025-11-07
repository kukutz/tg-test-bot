from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import get_settings
from app.services.markdown import markdown_to_html
from app.storage.models import Answer, Base

_ENGINE: AsyncEngine | None = None
_SESSION_FACTORY: async_sessionmaker[AsyncSession] | None = None


def _create_engine() -> AsyncEngine:
    global _ENGINE, _SESSION_FACTORY
    if _ENGINE is None:
        settings = get_settings()
        echo_flag = settings.environment == "development"
        _ENGINE = create_async_engine(settings.database_url, echo=echo_flag)
        _SESSION_FACTORY = async_sessionmaker(_ENGINE, expire_on_commit=False)
    return _ENGINE


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    if _SESSION_FACTORY is None:
        _create_engine()
    if _SESSION_FACTORY is None:
        raise RuntimeError("Session factory is not initialized")
    return _SESSION_FACTORY


async def init_db() -> None:
    engine = _create_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@asynccontextmanager
def session_scope() -> AsyncIterator[AsyncSession]:
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


class AnswerRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_answer(
        self,
        *,
        chat_id: str | None,
        message_id: int | None,
        inline_query_id: str | None,
        mode: str,
        prompt: str,
        answer_md: str,
        model: str,
        tokens_used: int | None = None,
    ) -> Answer:
        answer_html = markdown_to_html(answer_md)
        answer = Answer(
            chat_id=chat_id,
            message_id=message_id,
            inline_query_id=inline_query_id,
            mode=mode,
            prompt=prompt,
            answer_md=answer_md,
            answer_html=answer_html,
            model=model,
            tokens_used=tokens_used,
        )
        self._session.add(answer)
        await self._session.flush()
        return answer

    async def get_answer(self, answer_id: str) -> Answer | None:
        return await self._session.get(Answer, answer_id)

