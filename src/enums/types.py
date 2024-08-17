from enum import StrEnum


class AuthType(StrEnum):
    BEARER = "BEARER"
    WEBAPP_DATA = "WEBAPP_DATA"
    SESSION = "SESSION"
