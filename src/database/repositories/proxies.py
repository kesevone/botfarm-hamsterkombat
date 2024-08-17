from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Mapped

from .base import BaseRepository
from ..models import DBAccountProxy


class ProxiesRepository(BaseRepository):
    async def get_one(
        self,
        *relations: Mapped,
        proxy_id: Optional[int] = None,
        config_id: Optional[int] = None,
    ) -> Optional[DBAccountProxy]:
        self.statement = select(DBAccountProxy).where(
            (DBAccountProxy.id == proxy_id) | (proxy_id is None),
            (DBAccountProxy.config_id == config_id) | (config_id is None),
        )

        self.load(*relations)

        return await self._session.scalar(self.statement)

    async def get_all(
        self,
        *relations: Mapped,
        is_active: Optional[bool] = None,
        sort_column: Optional[Mapped] = None,
        limit_value: Optional[int] = None,
    ) -> list[Optional[DBAccountProxy]]:
        self.statement = select(DBAccountProxy).where(
            (DBAccountProxy.is_active == is_active) | (is_active is None)
        )

        self.load(*relations)
        self.sort(sort_column)
        self.limit(limit_value)

        results = await self._session.scalars(self.statement)
        return results.unique().all()
