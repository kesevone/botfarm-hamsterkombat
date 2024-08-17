from __future__ import annotations

from sqlalchemy import URL
from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    AsyncEngine,
    AsyncSession,
    create_async_engine,
)


def create_pool(
    dsn: str | URL, enable_logging: bool = False
) -> tuple[AsyncEngine, async_sessionmaker[AsyncSession]]:
    engine: AsyncEngine = create_async_engine(url=dsn, echo=enable_logging)
    return engine, async_sessionmaker(engine, expire_on_commit=False)
