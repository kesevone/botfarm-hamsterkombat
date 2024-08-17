from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Mapped

from .base import BaseRepository
from ..models import DBAccountUpgrade


class UpgradesRepository(BaseRepository):
    async def get_one(
        self,
        *relations: Mapped,
        upgrade_id: Optional[int] = None,
        upgrade_type: Optional[str] = None,
        section: Optional[str] = None,
        account_id: Optional[int] = None,
    ) -> Optional[DBAccountUpgrade]:
        self.statement = select(DBAccountUpgrade).where(
            (DBAccountUpgrade.id == upgrade_id) | (upgrade_id is None),
            (DBAccountUpgrade.type == upgrade_type) | (upgrade_type is None),
            (DBAccountUpgrade.section == section) | (section is None),
            (DBAccountUpgrade.account_id == account_id) | (account_id is None),
        )

        self.load(*relations)

        return await self._session.scalar(self.statement)

    async def get_all(
        self,
        *data: Mapped,
        account_id: Optional[int] = None,
        upgrade_type: Optional[str] = None,
        section: Optional[str] = None,
        is_expired: Optional[bool] = None,
        is_active: Optional[bool] = None,
        limit_value: Optional[int] = None,
    ) -> list[Optional[DBAccountUpgrade]]:
        self.statement = select(DBAccountUpgrade).where(
            (DBAccountUpgrade.type == upgrade_type) | (upgrade_type is None),
            (DBAccountUpgrade.section == section) | (section is None),
            (DBAccountUpgrade.account_id == account_id) | (account_id is None),
            (DBAccountUpgrade.is_expired == is_expired) | (is_expired is None),
            (DBAccountUpgrade.is_active == is_active) | (is_active is None),
        )
        self.load(*data)
        self.sort(*data)
        self.limit(limit_value)

        results = await self._session.scalars(self.statement)
        return results.unique().all()
