from aiogram.enums import ContentType
from aiogram_dialog import Dialog, ShowMode, Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import (
    Button,
    Group,
    Radio,
    ScrollingGroup,
    Select,
    SwitchTo,
    Url,
)
from aiogram_dialog.widgets.text import Const, Format, Jinja
from magic_filter import F

from src.enums import AuthType
from src.telegram.dialogs import states
from src.telegram.dialogs.common.texts import BACK_BUTTON_TEXT
from src.telegram.dialogs.common.widgets import (
    BACK_DIALOG_BUTTON,
    BACK_WINDOW_BUTTON,
    CUSTOM_SCROLL_BTNS,
    ID_SCROLL_NO_PAGER,
)
from src.telegram.dialogs.user.accounts import getters, handlers
from src.telegram.dialogs.user.configs.handlers import (
    on_start_account_config_dialog,
)

account_creator_dialog = Dialog(
    Window(
        Jinja(
            """
➡️ <b>Выберите</b> через что хотите <b>авторизовать</b> аккаунт:
            """
        ),
        Group(
            Button(
                Const("🔑 Bearer Токен"),
                id=AuthType.BEARER,
                on_click=handlers.on_switch_to_input_proxy_data,
            ),
            Button(
                Const("🌐 WebApp данные"),
                id=AuthType.WEBAPP_DATA,
                on_click=handlers.on_switch_to_input_proxy_data,
            ),
            Button(
                Const("📲 Телеграм Сессия"),
                id=AuthType.SESSION,
                on_click=handlers.on_switch_to_input_proxy_data,
            ),
            width=2,
        ),
        Url(
            Const("📝 Читать инструкцию"),
            Const("https://telegra.ph/Hamster-Fucker--Tutorial-06-08"),
        ),
        BACK_DIALOG_BUTTON,
        state=states.AccountCreatorDialog.SELECT_AUTH_TYPE,
    ),
    Window(
        Jinja(
            """
➡️ Установите <b>прокси для этого аккаунта</b>, иначе вы не сможете добавить его в ферму:

Необходим следущий формат прокси: <code>protocol://username:password@host:port</code>
            """
        ),
        MessageInput(handlers.on_switch_to_auth_type),
        SwitchTo(
            Const(BACK_BUTTON_TEXT),
            id="back_to_select_auth_type",
            state=states.AccountCreatorDialog.SELECT_AUTH_TYPE,
        ),
        state=states.AccountCreatorDialog.INPUT_PROXY_DATA,
    ),
    Window(
        Jinja(
            """
🔑 Вставьте <b>Bearer токен</b>, который есть у каждого аккаунта в <b>Hamster Kombat</b>.

Откройте <b>инструкцию</b> по кнопке ниже.
"""
        ),
        MessageInput(handlers.on_auth_with_webapp_or_bearer_data),
        SwitchTo(
            Const(BACK_BUTTON_TEXT),
            id="back_to_select_auth_type",
            state=states.AccountCreatorDialog.SELECT_AUTH_TYPE,
        ),
        state=states.AccountCreatorDialog.BEARER_TOKEN,
    ),
    Window(
        Jinja(
            """
🌐 Вставьте <b>данные WebApp</b>, которые генерируются в <b>хранилище вашей сессии</b>:

⚠️ Данный <b>способ авторизации</b> не безопасен.

Откройте <b>инструкцию</b> по кнопке ниже.
"""
        ),
        MessageInput(handlers.on_auth_with_webapp_or_bearer_data),
        SwitchTo(
            Const(BACK_BUTTON_TEXT),
            id="back_to_select_auth_type",
            state=states.AccountCreatorDialog.SELECT_AUTH_TYPE,
        ),
        state=states.AccountCreatorDialog.WEBAPP_DATA,
    ),
    Window(
        Jinja(
            """
📲 Отправьте файл с форматом <b>{ .session }</b>, наш бот <b>автоматически авторизуется</b> в Hamster Kombat и получит <b>необходимые данные</b>.

Мы не храним <b>ваши данные локально</b>, а используем их на текущий момент, <b>сохраняя в память</b>.
"""
        ),
        MessageInput(handlers.on_auth_with_session, content_types=ContentType.DOCUMENT),
        SwitchTo(
            Const(BACK_BUTTON_TEXT),
            id="back_to_select_auth_type",
            state=states.AccountCreatorDialog.SELECT_AUTH_TYPE,
        ),
        state=states.AccountCreatorDialog.SESSION,
    ),
)

account_dialog = Dialog(
    Window(
        Jinja(
            """
🐹 <b>Хомячок</b> {{ account.full_name }} (<code>{{ account.id }}</code>)
├ <b>Кол-во рефералов:</b> {{ account.referalls_count or 0 }}
├ <b>Уровень:</b> <code>{{ account.level }}</code>
├ <b>Баланс:</b> <code>{{ "{:,}".format(account.balance_coins | int) }}</code>
├ <b>Монет за всё время:</b> <code>{{ "{:,}".format(account.total_coins | int) }}</code>
├ <b>Монет за один тап:</b> <code>{{ account.earn_per_tap }}</code>
└ <b>Кол-во тапов, восполняемых в секунду:</b> <code>{{ account.taps_recover_per_sec }}</code>

👆 <b>Тапы</b>
├ <b>Доступно:</b> <code>{{ "{:,}".format(account.available_taps | int) }}</code>
└ <b>Максимум:</b> <code>{{ "{:,}".format(account.max_taps | int) }}</code>

💸 <b>Доход монет</b>
├ <b>В минуту:</b> <code>{{ "{:,}".format((account.earn_passive_per_sec * 60) | int) }}</code>
├ <b>В час:</b> <code>{{ "{:,}".format(account.earn_passive_per_hour | int) }}</code>
└ <b>В день:</b> <code>{{ "{:,}".format((account.earn_passive_per_hour * 24) | int) }}</code>

{% if daily_task %}
📆 <b>Ежедневная награда</b>
├ <b>День:</b> <code>{{ daily_task.days }}</code> 
├ <b>Вознаграждение:</b> <code>{{ "{:,}".format(daily_task.reward_coins | int) }}</code>
└ <b>Состояние:</b> <code>{{ 'Можно собрать' if not daily_task.is_completed else 'Собрана' }}</code>
{% else %}
📆 <b>Ежедневная награда</b>
└ <b>Состояние:</b> <code>Не удалось получить данные о ежедневной награде, попробуйте синхронизировать аккаунт</code>
{% endif %}

{% if cipher %}
📝 <b>Азбука Морзе</b>
├ <b>Вознаграждение:</b> <code>{{ "{:,}".format(cipher.bonus_coins | int) }}</code>
├ <b>Шифр:</b> <code>{{ cipher.cipher }}</code>
└ <b>Состояние:</b> <code>{{ 'Можно разгадать' if not cipher.is_claimed else 'Разгадан' }}</code>
{% else %}
📝 <b>Азбука Морзе</b>
└ <b>Состояние:</b> <code>Не удалось получить шифр, попробуйте синхронизировать аккаунт</code>
{% endif %}
        """
        ),
        Button(
            Const("👆 Тапнуть"),
            id="tap",
            when="is_proxy_active",
            on_click=handlers.on_button_tap,
        ),
        Button(
            Const("📝 Разгадать шифр"),
            id="cipher",
            when=~F["is_cipher_claimed"] & F["is_proxy_active"],
            on_click=handlers.on_claim_daily_cipher,
        ),
        Button(
            Const("⭐️ Собрать комбо"),
            id="combo",
            when=F["is_proxy_active"],
            on_click=handlers.on_claim_daily_combo,
        ),
        Button(
            Const("💰 Собрать награду"),
            id="daily_task",
            when=~F["is_daily_task_completed"] & F["is_proxy_active"],
            on_click=handlers.on_claim_daily_task,
        ),
        Button(
            Const("🔄 Синхронизовать"),
            id="sync",
            when="is_proxy_active",
            on_click=handlers.on_button_sync_data,
        ),
        Group(
            Button(
                Const("⏫ Бусты"),
                id="boosts",
                when="is_proxy_active",
                on_click=handlers.on_start_account_boosts_dialog,
            ),
            Button(
                Const("🎊 Апгрейды"),
                id="upgrades",
                when="is_proxy_active",
                on_click=handlers.on_start_account_upgrades_dialog,
            ),
            Button(
                Const("⚙️ Настройки"),
                id="config",
                on_click=on_start_account_config_dialog,
            ),
            width=2,
        ),
        # Url(
        #     Const("📝 Гайд по ферме"),
        #     Const("https://telegra.ph/Hamster-Fucker--Tutorial-06-08"),
        # ),
        Button(
            Const(BACK_BUTTON_TEXT),
            id="cancel",
            on_click=lambda e, w, manager: manager.done(
                show_mode=ShowMode.DELETE_AND_SEND
            ),
        ),
        getter=getters.get_account_data,
        state=states.AccountDialog.INFO,
    )
)


account_boosts_dialog = Dialog(
    Window(
        Jinja("⏫ Выберите <b>буст</b> для его покупки:"),
        ScrollingGroup(
            Select(
                Format("{item.name}"),
                id="boosts_selector",
                item_id_getter=lambda x: x.id,
                items="boosts",
                type_factory=int,
                on_click=handlers.on_select_boost_by_id,
            ),
            id=ID_SCROLL_NO_PAGER,
            width=1,
            height=10,
            hide_pager=True,
        ),
        CUSTOM_SCROLL_BTNS,
        Button(
            Const(BACK_BUTTON_TEXT),
            id="cancel",
            on_click=lambda e, w, manager: manager.done(
                show_mode=ShowMode.DELETE_AND_SEND
            ),
        ),
        getter=getters.get_account_boosts,
        state=states.AccountBoostsDialog.SELECT_BOOST,
    ),
    Window(
        Jinja(
            """
🐹 <b>Хомячок</b> {{ boost.account.full_name }} (<code>{{ boost.account.id }}</code>)
├ <b>Баланс:</b> <code>{{ "{:,}".format(boost.account.balance_coins | int) }}</code>
├ <b>Монет за один тап:</b> <code>{{ boost.account.earn_per_tap }}</code>

👆 <b>Тапы</b>
├ <b>Доступно:</b> <code>{{ "{:,}".format(boost.account.available_taps | int) }}</code>
└ <b>Максимум:</b> <code>{{ "{:,}".format(boost.account.max_taps | int) }}</code>

⏫ <b>Буст {{ boost.name }}</b> (<code>{{ boost.type }}</code>)
{% if boost.type == "BoostMaxTaps" %}
├ <b>Уровень:</b> <code>{{ boost.level }}</code>
├ <b>Стоимость:</b> <code>{{ boost.price | round(1) }}</code>
└ <b>Максимум тапов:</b> +<code>{{ boost.max_taps_delta }}</code>
{% elif boost.type == "BoostEarnPerTap" %}
├ <b>Уровень:</b> <code>{{ boost.level }}</code>
├ <b>Стоимость:</b> <code>{{ boost.price | round(1) }}</code>
└ <b>Монет за один тап:</b> +<code>{{ boost.earn_per_tap_delta }}</code>
{% elif boost.type == "BoostFullAvailableTaps" %}
{% if boost.cooldown_seconds > 0 %}
├ <b>Задержка:</b> <code>{{ boost.cooldown_seconds }}</code> сек.
{% endif %}
├ <b>Уровень:</b> <code>{{ boost.level }}</code>
└ <b>Стоимость:</b> <code>{{ boost.price | round(1) }}</code>
{% else %}
{% if boost.cooldown_seconds > 0 %}
├ <b>Задержка:</b> <code>{{ boost.cooldown_seconds }}</code> сек.
{% endif %}
├ <b>Уровень:</b> <code>{{ boost.level }}</code>
└ <b>Стоимость:</b> <code>{{ boost.price | round(1) }}</code>
{% endif %}

{% if boost.desc %}
📝 <b>Описание:</b> <code>{{ boost.desc }}</code>
{% endif %}
            """
        ),
        Button(
            Const("💰 Купить буст"),
            id="buy_boost",
            when="is_active",
            on_click=handlers.on_button_buy_boost,
        ),
        BACK_WINDOW_BUTTON,
        getter=getters.get_boost_data,
        state=states.AccountBoostsDialog.INFO,
    ),
)


account_upgrades_dialog = Dialog(
    Window(
        Jinja("🎊 Выберите <b>апгрейд</b> для его покупки:"),
        Radio(
            Format("☑️ {item}"),
            Format("⚪️ {item}"),
            id="sections_selector",
            item_id_getter=lambda x: x,
            items=["Markets", "PR&Team", "Legal", "Specials"],
            type_factory=str,
            on_click=handlers.on_select_upgrade_section,
        ),
        Button(
            Const("💰 Купить профитные"),
            id="profit_upgrades",
            on_click=handlers.on_button_buy_profit_upgrades,
        ),
        ScrollingGroup(
            Select(
                Format("{item.name}"),
                id="upgrades_selector",
                item_id_getter=lambda x: x.id,
                items="upgrades",
                type_factory=int,
                on_click=handlers.on_select_upgrade_by_id,
            ),
            id=ID_SCROLL_NO_PAGER,
            width=2,
            height=10,
            hide_pager=True,
        ),
        CUSTOM_SCROLL_BTNS,
        Button(
            Const(BACK_BUTTON_TEXT),
            id="cancel",
            on_click=lambda e, w, manager: manager.done(
                show_mode=ShowMode.DELETE_AND_SEND
            ),
        ),
        getter=getters.get_account_upgrades,
        state=states.AccountUpgradesDialog.SELECT_UPGRADE,
    ),
)


account_upgrade_dialog = Dialog(
    Window(
        Jinja(
            """
🐹 <b>Хомячок</b> {{ upgrade.account.full_name }} (<code>{{ upgrade.account.id }}</code>)
└ <b>Баланс:</b> <code>{{ "{:,}".format(upgrade.account.balance_coins | int) }}</code>

💸 <b>Доход монет</b>
├ <b>В минуту:</b> <code>{{ "{:,}".format((upgrade.account.earn_passive_per_sec * 60) | int) }}</code>
├ <b>В час:</b> <code>{{ "{:,}".format(upgrade.account.earn_passive_per_hour | int) }}</code>
└ <b>В день:</b> <code>{{ "{:,}".format((upgrade.account.earn_passive_per_hour * 24) | int) }}</code>

🎊 <b>Апгрейд {{ upgrade.name }}</b> (<code>{{ upgrade.type }}</code>)
{% if upgrade.cooldown_seconds > 0 %}
├ <b>Задержка:</b> <code>{{ upgrade.cooldown_seconds }}</code> сек.
{% endif %}
├ <b>Уровень:</b> <code>{{ upgrade.level }}</code>
{% if condition %}
├ <b>Зависит от:</b> <b>{{ condition.name }}</b> (<code>{{ condition.type }}</code>)
{% endif %}
├ <b>Раздел:</b> <code>{{ upgrade.section }}</code>
├ <b>Стоимость:</b> <code>{{ "{:,}".format(upgrade.price | int) }}</code>
├ <b>Монет за один час:</b> +<code>{{ "{:,}".format(upgrade.profit_per_hour | int) }}</code>
└ <b>Состояние:</b> <code>{{ '✅ Доступен для покупки' if is_active else '❌ Невозможно приобрести' }}</code>
            """
        ),
        Button(
            Const("💰 Купить апгрейд"),
            id="buy_upgrade",
            when="is_active",
            on_click=handlers.on_button_buy_upgrade,
        ),
        Button(
            Const("🔗 Открыть зависимый апгрейд"),
            id="open_condition",
            when="condition",
            on_click=handlers.on_start_upgrade_condition_dialog,
        ),
        Button(
            Const(BACK_BUTTON_TEXT),
            id="cancel",
            on_click=lambda e, w, manager: manager.done(
                show_mode=ShowMode.DELETE_AND_SEND
            ),
        ),
        getter=getters.get_upgrade_data,
        state=states.AccountUpgradeDialog.INFO,
    ),
)
