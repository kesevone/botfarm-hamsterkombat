from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Mapped

from .base import BaseRepository
from ..models import DBAccountBoost


class BoostsRepository(BaseRepository):
    async def get_one(
        self,
        *relations: Mapped,
        boost_id: Optional[int] = None,
        boost_type: Optional[str] = None,
        account_id: Optional[int] = None,
    ) -> Optional[DBAccountBoost]:
        self.statement = select(DBAccountBoost).where(
            (DBAccountBoost.id == boost_id) | (boost_id is None),
            (DBAccountBoost.type == boost_type) | (boost_type is None),
            (DBAccountBoost.account_id == account_id) | (account_id is None),
        )

        self.load(*relations)

        return await self._session.scalar(self.statement)

    async def get_all(
        self,
        *relations: Mapped,
        account_id: Optional[int] = None,
        boost_type: Optional[str] = None,
        sort_column: Optional[Mapped] = None,
        limit_value: Optional[int] = None,
    ) -> list[Optional[DBAccountBoost]]:
        self.statement = select(DBAccountBoost).where(
            (DBAccountBoost.type == boost_type) | (boost_type is None),
            (DBAccountBoost.account_id == account_id) | (account_id is None),
        )

        self.load(*relations)
        self.sort(sort_column)
        self.limit(limit_value)

        results = await self._session.scalars(self.statement)
        return results.unique().all()
