from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager, ShowMode
from aiogram_dialog.widgets.kbd import (
    Back,
    Button,
    Cancel,
    Group,
    Next,
    NextPage,
    PrevPage,
)
from aiogram_dialog.widgets.text import Const
from magic_filter import F

from src.telegram.dialogs.common import texts


async def on_button_close(_: CallbackQuery, __: Button, manager: DialogManager):
    return await manager.done(show_mode=ShowMode.DELETE_AND_SEND)


ID_SCROLL_NO_PAGER = "ID_SCROLL_NO_PAGER"
CANCEL_DIALOG_BUTTON = Button(
    Const(texts.CANCEL_BUTTON_TEXT),
    id="CLOSE_DIALOG",
    on_click=on_button_close,
)
BACK_DIALOG_BUTTON = Cancel(Const(texts.BACK_BUTTON_TEXT))
BACK_WINDOW_BUTTON = Back(Const(texts.BACK_BUTTON_TEXT))
NEXT_WINDOW_BUTTON = Next(Const(texts.FORWARD_BUTTON_TEXT))
CUSTOM_SCROLL_BTNS = Group(
    PrevPage(
        scroll=ID_SCROLL_NO_PAGER,
        text=Const(texts.ARROW_LEFT_BUTTON_TEXT),
        when=(F["current_page1"] > 1) & (F["pages"] > 1),
    ),
    NextPage(
        scroll=ID_SCROLL_NO_PAGER,
        text=Const(texts.ARROW_RIGHT_BUTTON_TEXT),
        when=(F["current_page1"] != F["pages"]) & (F["pages"] > 1),
    ),
    width=2,
)
