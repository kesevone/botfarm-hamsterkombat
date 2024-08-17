from aiogram.filters import BaseFilter
from aiogram.types import Message

from src.app_config import AppConfig
from src.database.models import DBUser


class IsAdminFilter(BaseFilter):
    async def __call__(self, _: Message, user: DBUser, config: AppConfig) -> bool:
        return user.id == config.common.develop_id
