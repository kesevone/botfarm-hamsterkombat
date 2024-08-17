from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from .models import Base


class UoW:
    _session: AsyncSession

    __slots__ = ("_session",)

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, *instances: Base, commit: Optional[bool] = False) -> None:
        self._session.add_all(instances)
        if commit:
            await self._session.commit()

    async def delete(self, *instances: Base, commit: Optional[bool] = True) -> None:
        for instance in instances:
            await self._session.delete(instance)

        if commit:
            await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()

    async def commit(self) -> None:
        await self._session.commit()
