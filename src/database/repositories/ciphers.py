from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Mapped

from .base import BaseRepository
from ..models import DBAccountCipher


class CiphersRepository(BaseRepository):
    async def get_one(
        self,
        *relations: Mapped,
        config_id: Optional[int] = None,
        account_id: Optional[int] = None,
    ) -> Optional[DBAccountCipher]:
        self.statement = select(DBAccountCipher).where(
            (DBAccountCipher.id == config_id) | (config_id is None),
            (DBAccountCipher.account_id == account_id) | (account_id is None),
        )

        self.load(*relations)

        return await self._session.scalar(self.statement)

    async def get_all(
        self,
        *relations: Mapped,
        is_claimed: Optional[bool] = None,
        sort_column: Optional[Mapped] = None,
        limit_value: Optional[int] = None,
    ) -> list[Optional[DBAccountCipher]]:
        self.statement = select(DBAccountCipher).where(
            (DBAccountCipher.is_claimed == is_claimed) | (is_claimed is None)
        )

        self.load(*relations)
        self.sort(sort_column)
        self.limit(limit_value)

        results = await self._session.scalars(self.statement)
        return results.unique().all()
