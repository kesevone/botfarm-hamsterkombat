from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Mapped

from .base import BaseRepository
from ..models import DBAccountAirdropTasks


class AirdropTasksRepository(BaseRepository):
    async def get_one(
        self, *relations: Mapped, user_id: int
    ) -> Optional[DBAccountAirdropTasks]:
        self.statement = select(DBAccountAirdropTasks).where(
            DBAccountAirdropTasks.id == user_id
        )

        self.load(*relations)

        return await self._session.scalar(self.statement)

    async def get_all(
        self,
        *relations: Mapped,
        sort_column: Optional[Mapped] = None,
        limit_value: Optional[int] = None,
    ) -> list[Optional[DBAccountAirdropTasks]]:
        self.statement = select(DBAccountAirdropTasks)

        self.load(*relations)
        self.sort(sort_column)
        self.limit(limit_value)

        results = await self._session.scalars(self.statement)
        return results.unique().all()
