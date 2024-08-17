from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class UserData(BaseModel):
    id: int
    first_name: str = Field(..., alias="firstName")
    last_name: str = Field(..., alias="lastName")
    username: Optional[str] = None

    def get_full_name(self) -> str:
        return f"{self.first_name} {self.last_name} "
