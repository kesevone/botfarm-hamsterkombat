from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Mapped

from .base import BaseRepository
from ..models import DBAccountTask


class TasksRepository(BaseRepository):
    async def get_one(
        self, *relations: Mapped, task_type: str, account_id: Optional[int] = None
    ) -> Optional[DBAccountTask]:
        self.statement = select(DBAccountTask).where(
            DBAccountTask.type == task_type,
            (DBAccountTask.account_id == account_id) | (account_id is None),
        )

        self.load(*relations)

        return await self._session.scalar(self.statement)

    async def get_all(
        self,
        *relations: Mapped,
        account_id: Optional[int] = None,
        task_type: Optional[str] = None,
        sort_column: Optional[Mapped] = None,
        limit_value: Optional[int] = None,
    ) -> list[Optional[DBAccountTask]]:
        self.statement = select(DBAccountTask).where(
            (DBAccountTask.type == task_type) | (task_type is None),
            (DBAccountTask.account_id == account_id) | (account_id is None),
        )

        self.load(*relations)
        self.sort(sort_column)
        self.limit(limit_value)

        results = await self._session.scalars(self.statement)
        return results.unique().all()
