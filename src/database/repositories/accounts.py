from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Mapped

from .base import BaseRepository
from ..models import DBAccount


class AccountsRepository(BaseRepository):
    async def get_one(
        self,
        *relations: Mapped,
        account_id: Optional[int] = None,
        user_id: Optional[int] = None,
    ) -> Optional[DBAccount]:
        self.statement = select(DBAccount).where(
            (DBAccount.id == account_id) | (account_id is None),
            (DBAccount.user_id == user_id) | (user_id is None),
        )

        self.load(*relations)

        return await self._session.scalar(self.statement)

    async def get_all(
        self,
        *data: Mapped,
        user_id: Optional[int] = None,
        limit_value: Optional[int] = None,
    ) -> list[Optional[DBAccount]]:
        self.statement = select(DBAccount).where(
            (DBAccount.user_id == user_id) | (user_id is None)
        )

        self.load(*data)
        self.sort(*data)
        self.limit(limit_value)

        results = await self._session.scalars(self.statement)
        return results.unique().all()
