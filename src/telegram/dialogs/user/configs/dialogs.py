from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button, Group, Radio, SwitchTo
from aiogram_dialog.widgets.text import Case, Const, Format, Jinja

from src.telegram.dialogs import states
from src.telegram.dialogs.common.texts import BACK_BUTTON_TEXT
from src.telegram.dialogs.common.widgets import BACK_DIALOG_BUTTON, BACK_WINDOW_BUTTON
from src.telegram.dialogs.user.configs import getters, handlers
from src.telegram.dialogs.user.configs.handlers import on_button_unlink_account

account_configs_dialog = Dialog(
    Window(
        Jinja(
            """
⚙️ Добро пожаловать в меню <b>управления настройками всех</b> аккаунтов!

<b>Все действия</b>, которые здесь присутствуют, будут выполняться <b>на всех аккаунтах</b>.
            """
        ),
        Group(
            Button(
                Const("💰 Собрать награду"),
                id="claim_daily_reward",
                on_click=handlers.on_button_claim_daily_reward_all,
            ),
            width=2,
        ),
        BACK_DIALOG_BUTTON,
        getter=getters.get_account_configs,
        state=states.AccountConfigsDialog.SELECT_CONFIG,
    )
)


account_config_dialog = Dialog(
    Window(
        Jinja(
            """
➡️ Выберите <b>модуль настроек</b> для его управлением:

⛏ <b>Авто-фарм</b>
├ <b>Активен:</b> <code>{{ 'Да' if is_autofarm else 'Нет' }}</code>
└ <b>Следующий запуск:</b> <code>{{ 'Неизвестно' if not next_run_autofarm else next_run_autofarm }}</code>

🎊 <b>Авто-апгрейд</b>
├ <b>Активен:</b> <code>{{ 'Да' if is_autoupgrade else 'Нет' }}</code>
└ <b>Следующий запуск:</b> <code>{{ 'Неизвестно' if not next_run_autoupgrade else next_run_autoupgrade }}</code>

🔄 <b>Авто-синхронизация:</b>
├ <b>Активен:</b> <code>{{ 'Да' if is_autosync else 'Нет' }}</code>
└ <b>Следующий запуск:</b> <code>{{ 'Неизвестно' if not next_run_autosync else next_run_autosync }}</code>

🌐 <b>Прокси</b>
{% if proxy is none or not proxy.is_active %}
└ ❗️ Не удалось <b>подключиться к прокси</b>.
{% else %}
└ ✅ <b>Прокси валидные</b>.
{% endif %}
            """
        ),
        Group(
            Button(
                Const("⛏ Авто-фарм"),
                id="start_autofarm",
                on_click=handlers.on_start_account_config_autofarm_dialog,
            ),
            Button(
                Const("🎊 Авто-апгрейд"),
                id="start_autoupgrade",
                on_click=handlers.on_start_account_config_autoupgrade_dialog,
            ),
            Button(
                Const("🔄 Авто-синхронизация"),
                id="start_autosync",
                on_click=handlers.on_start_account_config_autosync_dialog,
            ),
            Button(
                Const("🌐 Прокси"),
                id="start_proxy",
                on_click=handlers.on_start_account_config_proxy_dialog,
            ),
            width=2,
        ),
        Button(
            Const("➖ Отвязать аккаунт"),
            id="unlink",
            on_click=on_button_unlink_account,
        ),
        BACK_DIALOG_BUTTON,
        getter=getters.get_account_config,
        state=states.AccountConfigDialog.INFO,
    ),
    Window(
        Jinja(
            """
🎊 Вы можете <b>изменить процент монет на вашем балансе</b>, который будет отводиться на покупку апгрейдов <b>(авто-апгрейд)</b>.

<b>Баланс:</b> <code>{{ "{:,}".format(account.balance_coins | int) }}</code>
<b>Будет затрачено на апгрейд:</b> <code>{{ "{:,}".format(autoupgrade_limit | int) }}</code>
            """
        ),
        Radio(
            Format("☑️ {item}%"),
            Format("⚪️ {item}%"),
            id="autoupgrade_limit",
            item_id_getter=lambda x: x,
            items=["0", "25", "50", "75", "100"],
            type_factory=int,
            on_click=handlers.on_button_set_autoupgrade_limit,
        ),
        BACK_WINDOW_BUTTON,
        getter=getters.get_account_config,
        state=states.AccountConfigDialog.AUTOUPGRADE_LIMIT,
    ),
)


account_autofarm_config_dialog = Dialog(
    Window(
        Jinja(
            """
⛏ <b>Авто-фарм</b>
├ <b>Активен:</b> <code>{{ 'Да' if is_autofarm else 'Нет' }}</code>
├ <b>Уведомления:</b> <code>{{ 'Да' if is_autofarm_notifications else 'Нет' }}</code>
├ <b>Интервал запуска:</b> <code>{{ "{:,}".format((config.autofarm_interval // 60) | int) }}</code> мин.
└ <b>Следующий запуск:</b> <code>{{ 'Неизвестно' if not next_run_autofarm else next_run_autofarm }}</code>
            """
        ),
        Group(
            Button(
                Case(
                    {
                        None: Const("⚠️"),
                        True: Const("🔔"),
                        False: Const("🔕"),
                    },
                    selector="is_autofarm_notifications",
                ),
                id="autofarm_notifications",
                on_click=handlers.on_button_set_any_notifications,
            ),
            Button(
                Case(
                    {
                        None: Const("⚠️ Ошибка"),
                        True: Const("✅ Активен"),
                        False: Const("❌ Не активен:"),
                    },
                    selector="is_autofarm",
                ),
                id="autofarm",
                on_click=handlers.on_button_set_autofarm,
            ),
            when="is_proxy_active",
            width=2,
        ),
        BACK_DIALOG_BUTTON,
        getter=getters.get_account_config,
        state=states.AccountConfigAutofarmDialog.INFO,
    )
)


account_autoupgrade_config_dialog = Dialog(
    Window(
        Jinja(
            """
🎊 <b>Авто-апгрейд</b>
├ <b>Активен:</b> <code>{{ 'Да' if is_autoupgrade else 'Нет' }}</code>
├ <b>Уведомления:</b> <code>{{ 'Да' if is_autoupgrade_notifications else 'Нет' }}</code>
├ <b>Интервал запуска:</b> <code>{{ "{:,}".format((config.autoupgrade_interval // 60) | int) }}</code> мин.
└ <b>Следующий запуск:</b> <code>{{ 'Неизвестно' if not next_run_autoupgrade else next_run_autoupgrade }}</code>

{% if profit_upgrades %}
💰<b>Профитные апгрейды:</b>
{% for upgrade in profit_upgrades %}
• <code>{{ upgrade.type }}</code> | <b>Стоимость:</b> <code>{{ "{:,}".format(upgrade.price | int) }}</code> | До окупа: <code>{{ upgrade.profit_per_time | round(2) }}</code> ч.
{% endfor %}
{% endif %}
            """
        ),
        Group(
            Button(
                Case(
                    {
                        None: Const("⚠️"),
                        True: Const("🔔"),
                        False: Const("🔕"),
                    },
                    selector="is_autoupgrade_notifications",
                ),
                id="autoupgrade_notifications",
                on_click=handlers.on_button_set_any_notifications,
            ),
            Button(
                Case(
                    {
                        None: Const("⚠️ Ошибка"),
                        True: Const("✅ Активен"),
                        False: Const("❌ Не активен"),
                    },
                    selector="is_autoupgrade",
                ),
                id="autoupgrade",
                on_click=handlers.on_button_set_autoupgrade,
            ),
            when="is_proxy_active",
            width=2,
        ),
        BACK_DIALOG_BUTTON,
        getter=getters.get_account_config,
        state=states.AccountConfigAutoupgradeDialog.INFO,
    )
)


account_autosync_config_dialog = Dialog(
    Window(
        Jinja(
            """
🔄 <b>Авто-синхронизация:</b>
├ <b>Активен:</b> <code>{{ 'Да' if is_autosync else 'Нет' }}</code>
├ <b>Уведомления:</b> <code>{{ 'Да' if is_autosync_notifications else 'Нет' }}</code>
├ <b>Будет запущен через:</b> <code>{{ "{:,}".format((config.autosync_interval // 60) | int) }}</code> мин.
└ <b>Следующий запуск:</b> <code>{{ 'Неизвестно' if not next_run_autosync else next_run_autosync }}</code>
            """
        ),
        Group(
            Button(
                Case(
                    {
                        None: Const("⚠️"),
                        True: Const("🔔"),
                        False: Const("🔕"),
                    },
                    selector="is_autosync_notifications",
                ),
                id="autosync_notifications",
                on_click=handlers.on_button_set_any_notifications,
            ),
            Button(
                Case(
                    {
                        None: Const("⚠️ Ошибка"),
                        True: Const("✅ Активен"),
                        False: Const("❌ Не активен"),
                    },
                    selector="is_autosync",
                ),
                id="autosync",
                on_click=handlers.on_button_set_autosync,
            ),
            when="is_proxy_active",
            width=2,
        ),
        BACK_DIALOG_BUTTON,
        getter=getters.get_account_config,
        state=states.AccountConfigAutosyncDialog.INFO,
    )
)


account_proxy_config_dialog = Dialog(
    Window(
        Jinja(
            """
🌐 <b>Прокси</b>
{% if proxy is none %}
└ ❗️ Не удалось найти <b>активные прокси</b>, привяжите их для продолжения
{% else %}
├ <b>URL</b>: <code>{{ proxy.url }}</code>
├ <b>Протокол:</b> <code>{{ proxy.protocol }}</code>
├ <b>Хост:</b> <code>{{ proxy.host }}</code>
├ <b>Порт:</b> <code>{{ proxy.port }}</code>
├ <b>Логин:</b> <code>{{ proxy.username }}</code>
├ <b>Пароль:</b> <code>{{ proxy.password }}</code>
├ <b>Тайм-аут:</b> <code>{{ proxy.timeout }}</code> сек.
{% if not proxy.is_active %}
└ ❗️ Не удалось <b>подключиться к прокси</b>.
{% else %}
└ ✅ <b>Прокси валидные</b>.
{% endif %}
{% endif %}
            """
        ),
        Group(
            SwitchTo(
                Const("✏️ Изменить прокси"),
                id="set_proxy",
                state=states.AccountConfigProxyDialog.INPUT_PROXY_DATA,
            ),
            SwitchTo(
                Const("🕘 Установить тайм-аут"),
                id="set_timeout",
                state=states.AccountConfigProxyDialog.INPUT_TIMEOUT_SECONDS,
            ),
            Button(
                Const("🔎 Проверить"),
                id="check_proxy",
                on_click=handlers.on_button_check_proxy,
            ),
            width=2,
        ),
        BACK_DIALOG_BUTTON,
        getter=getters.get_account_config,
        state=states.AccountConfigProxyDialog.INFO,
    ),
    Window(
        Jinja(
            """
➡️ Отправьте <b>тайм-аут</b> в секундах для этого <b>прокси</b>:

Бот будет <b>пытаться в течении установленных секунд</b> сделать запросы к сайту, и если не удалось, то отключит <b>все автоматические функции</b> (авто-апгрейд, авто-фарм, авто-синхронизация).
            """
        ),
        MessageInput(handlers.on_input_timeout_seconds),
        SwitchTo(
            Const(BACK_BUTTON_TEXT),
            id="back_to_info",
            state=states.AccountConfigProxyDialog.INFO,
        ),
        state=states.AccountConfigProxyDialog.INPUT_TIMEOUT_SECONDS,
    ),
    Window(
        Jinja(
            """
➡️ Отправьте новый <b>прокси для этого аккаунта</b>:

Необходим следущий формат прокси: <code>protocol://username:password@host:port</code>
            """
        ),
        MessageInput(handlers.on_input_proxy_data),
        SwitchTo(
            Const(BACK_BUTTON_TEXT),
            id="back_to_info",
            state=states.AccountConfigProxyDialog.INFO,
        ),
        state=states.AccountConfigProxyDialog.INPUT_PROXY_DATA,
    ),
)
