from contextlib import suppress
from typing import Optional

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.types import Message, ReplyKeyboardMarkup
from aiogram_dialog import DialogManager, ShowMode, StartMode
from redis.asyncio import Redis

from src.app_config import AppConfig
from src.database import (
    Repository,
    UoW,
)
from src.database.models import (
    DBUser,
)
from src.telegram.dialogs import states
from src.telegram.dialogs.common import texts as common_texts
from src.telegram.filters import IsAdminFilter
from src.telegram.keyboards import build_reply_keyboard
from src.utils.redis import process_message

user_router = Router()
admin_router = Router()
admin_router.message.filter(IsAdminFilter())


@user_router.message(CommandStart())
@user_router.message(F.text == common_texts.MAIN_MENU_BTN_TEXT)
async def on_start_welcome_dialog(_: Message, dialog_manager: DialogManager):
    redis: Redis = dialog_manager.middleware_data["redis"]
    user_id: int = dialog_manager.event.from_user.id
    kb: ReplyKeyboardMarkup = build_reply_keyboard(common_texts.MAIN_MENU_BTN_TEXT)

    new_message: Message = await dialog_manager.event.answer(text="👋", reply_markup=kb)
    old_message_id: int = await process_message(
        redis=redis, user_id=user_id, new_message_id=new_message.message_id
    )
    if old_message_id:
        with suppress(TelegramForbiddenError, TelegramBadRequest):
            await dialog_manager.event.bot.delete_message(
                chat_id=user_id, message_id=old_message_id
            )

    await dialog_manager.event.delete()
    return await dialog_manager.start(
        states.GeneralDialog.WELCOME,
        show_mode=ShowMode.DELETE_AND_SEND,
        mode=StartMode.RESET_STACK,
    )


@admin_router.message(Command("is_user_active"))
async def on_set_is_active(
    _: Message,
    dialog_manager: DialogManager,
    repo: Repository,
    uow: UoW,
    config: AppConfig,
    command: CommandObject,
):
    if not command.args:
        return

    target_user_id: int = int(command.args)
    if target_user_id == config.common.develop_id:
        return await dialog_manager.event.answer("You can't set yourself active.")

    user: DBUser = await repo.users.get_one(user_id=target_user_id)
    user.set_is_active(is_active=not user.is_active)
    await uow.add(user, commit=True)

    return await dialog_manager.event.answer(
        f"Success, user: {user.id} | status: {user.is_active}"
    )


@admin_router.message(Command("set_max_accounts"))
async def on_set_account_limit(
    _: Message,
    dialog_manager: DialogManager,
    repo: Repository,
    uow: UoW,
    command: CommandObject,
):
    if not command.args:
        return

    data: list[str] = command.args.split(" ")
    if len(data) != 2:
        return

    target_user_id: int = int(data[0])
    limit: int = int(data[1])
    user: Optional[DBUser] = await repo.users.get_one(user_id=target_user_id)
    if user is None:
        return await dialog_manager.event.answer("User not found.")

    user.set_max_accounts(max_accounts=limit)
    await uow.add(user, commit=True)
    return await dialog_manager.event.answer(
        f"Success, user: {user.id} | max_accounts: {user.max_accounts}"
    )


@admin_router.message(Command("send"))
async def on_send_mailing(_: Message, dialog_manager: DialogManager, repo: Repository):
    text = dialog_manager.event.html_text.replace("/send", "")
    if not text:
        return

    users: list[Optional[DBUser]] = await repo.users.get_all()
    for user in users:
        try:
            await dialog_manager.event.bot.send_message(chat_id=user.id, text=text)
        except:
            pass
