from aiogram.types import User
from aiogram.utils.link import create_tg_link
from aiogram_dialog import DialogManager

from src.database.models import DBUser


async def get_user_data(dialog_manager: DialogManager, **_):
    """
    Get user data from an aiogram event and middleware data.
    """
    db_user: DBUser = dialog_manager.middleware_data["user"]
    user: User = dialog_manager.event.from_user
    return {
        "db_user": db_user,
        "user_id": user.id,
        "username": user.username,
        "fullname": user.full_name,
        "user_link": create_tg_link("user", id=user.id),
    }
