from __future__ import annotations

from typing import Any, Optional

from sqlalchemy import Select, UnaryExpression
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, selectinload


class BaseRepository:
    _session: AsyncSession
    statement: Select | Any

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self.statement = None

    def load(self, *relations: Mapped) -> None:
        if not relations:
            return

        self.statement = self.statement.options(
            *[
                selectinload(relation)
                for relation in relations
                if not isinstance(relation, (UnaryExpression,))
            ]
        )

    def sort(self, *columns: Mapped) -> None:
        if not columns:
            return

        self.statement = self.statement.order_by(
            *[column for column in columns if isinstance(column, (UnaryExpression,))]
        )

    def limit(self, value: Optional[int] = None) -> None:
        if not value:
            return

        self.statement = self.statement.limit(limit=value)
