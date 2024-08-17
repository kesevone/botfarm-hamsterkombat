from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Button, ScrollingGroup, Select
from aiogram_dialog.widgets.text import Const, Jinja
from magic_filter import F

from src.telegram.dialogs import states
from src.telegram.dialogs.common.widgets import CUSTOM_SCROLL_BTNS, ID_SCROLL_NO_PAGER
from src.telegram.dialogs.user.accounts.getters import get_accounts_by_user_id
from src.telegram.dialogs.user.accounts.handlers import (
    on_select_account_by_id,
    on_start_account_creator_dialog,
)
from src.telegram.dialogs.user.configs.handlers import on_start_account_configs_dialog

general_dialog = Dialog(
    Window(
        Jinja(
            """
👋 Добро пожаловать в <b>Hamster Fucker</b>!

За ваши аккаунты (в игре <b>Hamster Kombat</b>, не в <b>Telegram</b>) мы ответственности <b>не несём</b>.

<b>Лимит аккаунтов</b>, которые можно добавить в ферму: {{ user.max_accounts }}
            """
        ),
        Button(
            Const("➕ Добавить аккаунт"),
            id="add_account",
            when=~F["is_accounts_limit"],
            on_click=on_start_account_creator_dialog,
        ),
        Button(
            Const("⚙️ Общие настройки"),
            id="configs",
            when="accounts",
            on_click=on_start_account_configs_dialog,
        ),
        ScrollingGroup(
            Select(
                Jinja(
                    "{{ item.full_name }} | {{ '{:,}'.format(item.balance_coins | int) }}"
                ),
                id="accounts_selector",
                item_id_getter=lambda x: x.id,
                items="accounts",
                type_factory=int,
                on_click=on_select_account_by_id,
            ),
            id=ID_SCROLL_NO_PAGER,
            width=1,
            height=10,
            hide_pager=True,
        ),
        CUSTOM_SCROLL_BTNS,
        getter=get_accounts_by_user_id,
        state=states.GeneralDialog.WELCOME,
    )
)
