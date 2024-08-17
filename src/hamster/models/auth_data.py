from typing import Optional

from pydantic import BaseModel, Field


class AuthData(BaseModel):
    auth_token: Optional[str] = Field(None, alias="authToken")
    status: Optional[str] = None
