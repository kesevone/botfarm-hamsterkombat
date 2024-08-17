from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Mapped

from .base import BaseRepository
from ..models import DBAccountConfig


class ConfigsRepository(BaseRepository):
    async def get_one(
        self,
        *relations: Mapped,
        config_id: Optional[int] = None,
        account_id: Optional[int] = None,
    ) -> Optional[DBAccountConfig]:
        self.statement = select(DBAccountConfig).where(
            (DBAccountConfig.id == config_id) | (config_id is None),
            (DBAccountConfig.account_id == account_id) | (account_id is None),
        )

        self.load(*relations)

        return await self._session.scalar(self.statement)

    async def get_all(
        self,
        *relations: Mapped,
        user_id: Optional[int] = None,
        is_autofarm: Optional[bool] = None,
        is_autoupgrade: Optional[bool] = None,
        is_active: Optional[bool] = None,
        sort_column: Optional[Mapped] = None,
        limit_value: Optional[int] = None,
    ) -> list[Optional[DBAccountConfig]]:
        self.statement = select(DBAccountConfig).where(
            (DBAccountConfig.account.user_id == user_id) | (user_id is None),
            (DBAccountConfig.is_autofarm == is_autofarm) | (is_autofarm is None),
            (DBAccountConfig.is_autoupgrade == is_autoupgrade)
            | (is_autoupgrade is None),
            (DBAccountConfig.is_active == is_active) | (is_active is None),
        )

        self.load(*relations)
        self.sort(sort_column)
        self.limit(limit_value)

        results = await self._session.scalars(self.statement)
        return results.unique().all()
