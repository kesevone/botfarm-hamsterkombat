from __future__ import annotations

from typing import Any, Awaitable, Callable, Optional

from aiogram import BaseMiddleware
from aiogram.types import Chat, TelegramObject, User

from src.app_config import AppConfig
from src.database import Repository, UoW
from src.database.models import DBUser


class UserMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Optional[Any]:
        aiogram_user: Optional[User] = data.get("event_from_user")
        aiogram_chat: Optional[Chat] = data.get("event_chat")
        if aiogram_user is None or aiogram_chat is None or aiogram_user.is_bot:
            return await handler(event, data)

        repo: Repository = data["repo"]
        uow: UoW = data["uow"]
        config: AppConfig = data["config"]

        user: Optional[DBUser] = await repo.users.get_one(user_id=aiogram_user.id)
        if user is None:
            user: DBUser = DBUser.create(
                user_id=aiogram_user.id,
                full_name=aiogram_user.full_name,
                username=aiogram_user.username,
                is_active=False,
            )
            await uow.add(user, commit=True)

        if not user.is_active:
            if user.id == config.common.develop_id:
                user.set_is_active(is_active=True)
            else:
                return await event.message.answer(
                    """
🚫 <b>Доступ ограничен.</b> Приобретите его у владельца бота.
                    """
                )

        data["user"] = user
        return await handler(event, data)
