from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from src.database import SQLSessionContext


class DBSessionMiddleware(BaseMiddleware):
    session: async_sessionmaker[AsyncSession]

    __slots__ = ("session_pool",)

    def __init__(self, session: async_sessionmaker[AsyncSession]) -> None:
        self.session = session

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        async with SQLSessionContext(session_pool=self.session) as (repository, uow):
            data["repo"] = repository
            data["uow"] = uow
            return await handler(event, data)
