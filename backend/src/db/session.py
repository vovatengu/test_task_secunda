from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from core.settings import Settings, get_settings

_session_maker: async_sessionmaker[AsyncSession] | None = None


def create_async_engine_from_settings(settings: Settings | None = None) -> AsyncEngine:
    cfg = settings or get_settings()
    return create_async_engine(
        cfg.database_url,
        echo=False,
        pool_pre_ping=True,
    )


def async_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )


def bind_session_maker(maker: async_sessionmaker[AsyncSession]) -> None:
    global _session_maker
    _session_maker = maker


def get_session_maker() -> async_sessionmaker[AsyncSession]:
    if _session_maker is None:
        msg = "Database session maker is not configured; call bind_session_maker() at startup"
        raise RuntimeError(msg)
    return _session_maker


async def get_db() -> AsyncIterator[AsyncSession]:
    if _session_maker is None:
        msg = "Database session maker is not configured; call bind_session_maker() at startup"
        raise RuntimeError(msg)
    async with _session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
