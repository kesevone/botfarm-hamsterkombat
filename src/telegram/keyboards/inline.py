from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


class ActionCallbackFactory(CallbackData, prefix="fabaction"):
    action: str
    chat_id: str
    user_id: str


def build_inline_keyboard(
    *texts: tuple[str, ActionCallbackFactory], row_width: int = 2
) -> InlineKeyboardMarkup:
    if not texts:
        return None

    builder: InlineKeyboardBuilder = InlineKeyboardBuilder()
    for text in texts:
        builder.button(text=text[0], callback_data=text[1])

    builder.adjust(row_width)
    return builder.as_markup()
