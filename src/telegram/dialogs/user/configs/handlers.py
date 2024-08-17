import asyncio
import random
from typing import Any, Optional

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager, ShowMode
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button, ManagedCheckbox, ManagedRadio
from aiohttp_socks import ProxyConnector
from apscheduler import AsyncScheduler
from apscheduler.triggers.interval import IntervalTrigger

from src.app_config import AppConfig
from src.database import Repository, UoW
from src.database.models import DBAccount, DBAccountConfig, DBAccountProxy
from src.enums import SchedulerActions, TaskIds
from src.hamster import (
    add_schedule,
    generate_schedule_id,
    HamsterKombat,
    process_schedule,
    RequestError,
)
from src.telegram.dialogs import states
from src.telegram.dialogs.common import texts as common_texts
from src.telegram.dialogs.user.accounts.handlers import (
    disable_account_proxy,
    sync_account,
    sync_tasks,
)
from src.utils.formatters import calculate_autofarm_interval
from src.utils.loggers import service
from src.utils.parse_proxy import parse_proxy_from_string, ProxyData


async def on_start_account_configs_dialog(
    _: CallbackQuery, __: Button, manager: DialogManager
):
    return await manager.start(states.AccountConfigsDialog.SELECT_CONFIG)


async def on_start_account_config_dialog(
    _: CallbackQuery, __: Button, manager: DialogManager
):
    data: dict[str, Any] = {"account_id": manager.start_data["account_id"]}
    return await manager.start(states.AccountConfigDialog.INFO, data=data)


async def on_switch_to_autoupgrade_limit_dialog(
    _: CallbackQuery, __: Button, manager: DialogManager
):
    return await manager.switch_to(states.AccountConfigDialog.AUTOUPGRADE_LIMIT)


async def on_start_account_config_autofarm_dialog(
    _: CallbackQuery, __: Button, manager: DialogManager
):
    data: dict[str, Any] = {"account_id": manager.start_data["account_id"]}
    return await manager.start(states.AccountConfigAutofarmDialog.INFO, data=data)


async def on_start_account_config_autoupgrade_dialog(
    _: CallbackQuery, __: Button, manager: DialogManager
):
    data: dict[str, Any] = {"account_id": manager.start_data["account_id"]}
    return await manager.start(states.AccountConfigAutoupgradeDialog.INFO, data=data)


async def on_start_account_config_autosync_dialog(
    _: CallbackQuery, __: Button, manager: DialogManager
):
    data: dict[str, Any] = {"account_id": manager.start_data["account_id"]}
    return await manager.start(states.AccountConfigAutosyncDialog.INFO, data=data)


async def on_start_account_config_proxy_dialog(
    _: CallbackQuery, __: Button, manager: DialogManager
):
    data: dict[str, Any] = {"account_id": manager.start_data["account_id"]}
    return await manager.start(states.AccountConfigProxyDialog.INFO, data=data)


async def on_button_disable_all(_: CallbackQuery, __: Button, manager: DialogManager):
    repo: Repository = manager.middleware_data["repo"]
    sched: AsyncScheduler = manager.middleware_data["sched"]
    uow: UoW = manager.middleware_data["uow"]
    user_id: int = manager.event.from_user.id
    accounts: list[Optional[DBAccount]] = await repo.accounts.get_all(
        DBAccount.config, user_id=user_id
    )
    for account in accounts:
        account.config.set_is_autofarm(is_autofarm=False)
        account.config.set_is_autoupgrade(is_autoupgrade=False)

        await process_schedule(
            sched=sched,
            action=SchedulerActions.REMOVE,
            account=account,
            task_id=TaskIds.AUTOFARM,
            schedule_id=generate_schedule_id(
                task_id=TaskIds.AUTOFARM, account_id=account.id, user_id=account.user_id
            ),
        )
        await process_schedule(
            sched=sched,
            action=SchedulerActions.REMOVE,
            account=account,
            task_id=TaskIds.AUTOUPGRADE,
            schedule_id=generate_schedule_id(
                task_id=TaskIds.AUTOUPGRADE,
                account_id=account.id,
                user_id=account.user_id,
            ),
        )

        await uow.add(account.config)

    await uow.commit()
    return await manager.event.answer(common_texts.SUCCESS_TEXT)


async def on_button_set_autofarm(_: CallbackQuery, __: Button, manager: DialogManager):
    repo: Repository = manager.middleware_data["repo"]
    sched: AsyncScheduler = manager.middleware_data["sched"]
    uow: UoW = manager.middleware_data["uow"]
    account_id: int = manager.start_data["account_id"]
    account: Optional[DBAccount] = await repo.accounts.get_one(
        DBAccount.config, account_id=account_id
    )
    account.config.set_is_autofarm(is_autofarm=not account.config.is_autofarm)
    schedule_id: str = generate_schedule_id(
        task_id=TaskIds.AUTOFARM, account_id=account.id, user_id=account.user_id
    )
    if account.config.is_autofarm:
        await add_schedule(
            sched=sched,
            trigger=IntervalTrigger(
                seconds=calculate_autofarm_interval(
                    available_taps=account.available_taps,
                    max_taps=account.max_taps,
                    taps_recover_per_sec=account.taps_recover_per_sec,
                ),
            ),
            schedule_id=schedule_id,
            task_id=TaskIds.AUTOFARM,
            account_id=account.id,
        )
    else:
        await process_schedule(
            sched=sched,
            action=SchedulerActions.REMOVE,
            schedule_id=schedule_id,
            task_id=TaskIds.AUTOFARM,
        )

    await uow.add(account.config, account, commit=True)
    return await manager.event.answer(common_texts.SUCCESS_TEXT)


async def on_button_set_any_notifications(
    _: CallbackQuery, widget: Button, manager: DialogManager
):
    repo: Repository = manager.middleware_data["repo"]
    uow: UoW = manager.middleware_data["uow"]
    widget_id: Optional[str] = widget.widget_id
    account_id: int = manager.start_data["account_id"]
    account: Optional[DBAccount] = await repo.accounts.get_one(
        DBAccount.config, account_id=account_id
    )
    if widget_id == "autofarm_notifications":
        account.config.set_autofarm_notifications(
            is_autofarm_notifications=not account.config.is_autofarm_notifications
        )
    elif widget_id == "autoupgrade_notifications":
        account.config.set_autoupgrade_notifications(
            is_autoupgrade_notifications=not account.config.is_autoupgrade_notifications
        )
    elif widget_id == "autosync_notifications":
        account.config.set_autosync_notifications(
            is_autosync_notifications=not account.config.is_autosync_notifications
        )
    else:
        return await manager.event.answer(common_texts.ERROR_TEXT)

    return await uow.add(account.config, commit=True)


async def on_button_set_autoupgrade(
    _: CallbackQuery, __: Button, manager: DialogManager
):
    repo: Repository = manager.middleware_data["repo"]
    uow: UoW = manager.middleware_data["uow"]
    sched: AsyncScheduler = manager.middleware_data["sched"]
    account_id: int = manager.start_data["account_id"]
    account: Optional[DBAccount] = await repo.accounts.get_one(
        DBAccount.config, account_id=account_id
    )
    account.config.set_is_autoupgrade(is_autoupgrade=not account.config.is_autoupgrade)
    schedule_id: str = generate_schedule_id(
        task_id=TaskIds.AUTOUPGRADE, account_id=account.id, user_id=account.user_id
    )
    if account.config.is_autoupgrade:
        await add_schedule(
            sched=sched,
            trigger=IntervalTrigger(
                seconds=account.config.autoupgrade_interval,
            ),
            schedule_id=generate_schedule_id(
                task_id=TaskIds.AUTOUPGRADE,
                account_id=account.id,
                user_id=account.user_id,
            ),
            task_id=TaskIds.AUTOUPGRADE,
            account_id=account.id,
        )
    else:
        await process_schedule(
            sched=sched,
            schedule_id=schedule_id,
            task_id=TaskIds.AUTOUPGRADE,
            action=SchedulerActions.REMOVE,
        )

    await uow.add(account.config, commit=True)
    return await manager.event.answer(common_texts.SUCCESS_TEXT)


async def on_button_set_autosync(_: CallbackQuery, __: Button, manager: DialogManager):
    repo: Repository = manager.middleware_data["repo"]
    uow: UoW = manager.middleware_data["uow"]
    sched: AsyncScheduler = manager.middleware_data["sched"]
    account_id: int = manager.start_data["account_id"]
    account: Optional[DBAccount] = await repo.accounts.get_one(
        DBAccount.config, account_id=account_id
    )
    account.config.set_is_autosync(is_autosync=not account.config.is_autosync)
    schedule_id: str = generate_schedule_id(
        task_id=TaskIds.AUTOSYNC, account_id=account.id, user_id=account.user_id
    )
    if account.config.is_autosync:
        await add_schedule(
            sched=sched,
            trigger=IntervalTrigger(
                seconds=account.config.autosync_interval,
            ),
            schedule_id=generate_schedule_id(
                task_id=TaskIds.AUTOSYNC,
                account_id=account.id,
                user_id=account.user_id,
            ),
            task_id=TaskIds.AUTOSYNC,
            account_id=account.id,
        )
    else:
        await process_schedule(
            sched=sched,
            schedule_id=schedule_id,
            task_id=TaskIds.AUTOSYNC,
            action=SchedulerActions.REMOVE,
        )

    await uow.add(account.config, commit=True)
    return await manager.event.answer(common_texts.SUCCESS_TEXT)


async def on_button_set_autoupgrade_all(
    _: CallbackQuery, checkbox: ManagedCheckbox, manager: DialogManager
):
    repo: Repository = manager.middleware_data["repo"]
    sched: AsyncScheduler = manager.middleware_data["sched"]
    uow: UoW = manager.middleware_data["uow"]
    user_id: int = manager.event.from_user.id
    accounts: list[Optional[DBAccount]] = await repo.accounts.get_all(
        DBAccount.config, user_id=user_id
    )
    for account in accounts:
        account.config.set_is_autoupgrade(is_autoupgrade=not checkbox.is_checked())
        schedule_id: str = (
            generate_schedule_id(
                task_id=TaskIds.AUTOUPGRADE,
                account_id=account.id,
                user_id=account.user_id,
            ),
        )
        if account.config.is_autoupgrade:
            await add_schedule(
                sched=sched,
                trigger=IntervalTrigger(seconds=account.config.autoupgrade_interval),
                schedule_id=schedule_id,
                task_id=TaskIds.AUTOUPGRADE,
                account_id=account.id,
            )
        else:
            await process_schedule(
                sched=sched,
                schedule_id=schedule_id,
                task_id=TaskIds.AUTOUPGRADE,
                action=SchedulerActions.REMOVE,
            )

        await uow.add(account.config)

    await uow.commit()
    return await manager.event.answer(common_texts.SUCCESS_TEXT)


async def on_button_set_autoupgrade_limit(
    _: CallbackQuery, __: ManagedRadio, manager: DialogManager, percent: int
):
    repo: Repository = manager.middleware_data["repo"]
    uow: UoW = manager.middleware_data["uow"]
    account_id: int = manager.start_data["account_id"]
    account: Optional[DBAccount] = await repo.accounts.get_one(
        DBAccount.config, account_id=account_id
    )
    account.config.set_limit_percent(limit_percent=percent)
    await uow.add(account.config, commit=True)


async def on_button_set_autosync_all(
    _: CallbackQuery, checkbox: ManagedCheckbox, manager: DialogManager
):
    repo: Repository = manager.middleware_data["repo"]
    sched: AsyncScheduler = manager.middleware_data["sched"]
    uow: UoW = manager.middleware_data["uow"]
    user_id: int = manager.event.from_user.id
    accounts: list[Optional[DBAccount]] = await repo.accounts.get_all(
        DBAccount.config, user_id=user_id
    )
    for account in accounts:
        account.config.set_is_autosync(is_autosync=not checkbox.is_checked())
        schedule_id: str = generate_schedule_id(
            task_id=TaskIds.AUTOSYNC,
            account_id=account.id,
            user_id=account.user_id,
        )
        if account.config.is_autosync:
            await add_schedule(
                sched=sched,
                trigger=IntervalTrigger(seconds=account.config.autosync_interval),
                schedule_id=schedule_id,
                task_id=TaskIds.AUTOSYNC,
                account_id=account.id,
            )
        else:
            await process_schedule(
                sched=sched,
                schedule_id=schedule_id,
                task_id=TaskIds.AUTOSYNC,
                action=SchedulerActions.REMOVE,
            )

        await uow.add(account.config)

    await uow.commit()
    return await manager.event.answer(common_texts.SUCCESS_TEXT)


async def on_button_set_notifications_all(
    _: CallbackQuery, checkbox: ManagedCheckbox, manager: DialogManager
):
    repo: Repository = manager.middleware_data["repo"]
    uow: UoW = manager.middleware_data["uow"]
    user_id: int = manager.event.from_user.id
    accounts: list[Optional[DBAccount]] = await repo.accounts.get_all(
        DBAccount.config, user_id=user_id
    )
    for account in accounts:
        account.config.set_is_notifications(is_notifications=not checkbox.is_checked())
        await uow.add(account.config)

    await uow.commit()
    return await manager.event.answer(common_texts.SUCCESS_TEXT)


async def on_button_unlink_account(
    _: CallbackQuery, __: Button, manager: DialogManager
):
    repo: Repository = manager.middleware_data["repo"]
    uow: UoW = manager.middleware_data["uow"]
    sched: AsyncScheduler = manager.middleware_data["sched"]
    account_id: int = manager.start_data["account_id"]
    account: Optional[DBAccount] = await repo.accounts.get_one(
        DBAccount.config, account_id=account_id
    )

    await process_schedule(
        sched=sched,
        action=SchedulerActions.REMOVE,
        schedule_id=generate_schedule_id(
            task_id=TaskIds.AUTOFARM, account_id=account.id, user_id=account.user_id
        ),
        task_id=TaskIds.AUTOFARM,
    )
    await process_schedule(
        sched=sched,
        action=SchedulerActions.REMOVE,
        schedule_id=generate_schedule_id(
            task_id=TaskIds.AUTOUPGRADE, account_id=account.id, user_id=account.user_id
        ),
        task_id=TaskIds.AUTOUPGRADE,
    )
    await process_schedule(
        sched=sched,
        action=SchedulerActions.REMOVE,
        schedule_id=generate_schedule_id(
            task_id=TaskIds.AUTOSYNC, account_id=account.id, user_id=account.user_id
        ),
        task_id=TaskIds.AUTOSYNC,
    )
    account.config.set_is_autofarm(is_autofarm=False)
    account.config.set_is_autoupgrade(is_autoupgrade=False)
    account.config.set_is_autosync(is_autosync=False)
    account.config.set_is_active(is_active=False)
    account.set_data(user_id=None)

    await uow.add(account, account.config, commit=True)
    await manager.event.answer(common_texts.SUCCESS_TEXT)
    await manager.done(show_mode=ShowMode.NO_UPDATE)
    return await manager.done(show_mode=ShowMode.DELETE_AND_SEND)


async def on_button_check_proxy(_: CallbackQuery, __: Button, manager: DialogManager):
    repo: Repository = manager.middleware_data["repo"]
    uow: UoW = manager.middleware_data["uow"]
    hamster: HamsterKombat = manager.middleware_data["hamster"]
    config: AppConfig = manager.middleware_data["config"]

    account_id: int = manager.start_data["account_id"]
    account: Optional[DBAccount] = await repo.accounts.get_one(
        DBAccount.config, account_id=account_id
    )

    account_proxy: Optional[DBAccountProxy] = await repo.proxies.get_one(
        config_id=account.config.id
    )
    if account_proxy is None:
        return await manager.event.answer(common_texts.PROXY_NOT_FOUND_TEXT)

    proxy_connector: ProxyConnector = ProxyConnector.from_url(account_proxy.url)
    if not await hamster.check_proxy(
        proxy_connector=proxy_connector,
        real_ip=config.common.server_ip,
        response_timeout=account_proxy.timeout,
    ):
        return await manager.event.answer(common_texts.BAD_PROXY_DATA_TEXT)
    else:
        account_proxy.set_data(is_active=True)
        await uow.add(account_proxy, commit=True)
        return await manager.event.answer(common_texts.SUCCESS_TEXT)


async def on_input_timeout_seconds(
    _: Message, __: MessageInput, manager: DialogManager
):
    repo: Repository = manager.middleware_data["repo"]
    uow: UoW = manager.middleware_data["uow"]

    account_id: int = manager.start_data["account_id"]
    timeout = int(manager.event.text)

    config: Optional[DBAccountConfig] = await repo.configs.get_one(
        account_id=account_id
    )
    account_proxy: Optional[DBAccountProxy] = await repo.proxies.get_one(
        config_id=config.id
    )
    account_proxy.set_data(timeout=timeout)

    await uow.add(account_proxy, commit=True)
    await manager.event.answer(common_texts.SUCCESS_TEXT)
    return await manager.switch_to(states.AccountConfigProxyDialog.INFO)


async def on_input_proxy_data(_: Message, __: MessageInput, manager: DialogManager):
    repo: Repository = manager.middleware_data["repo"]
    uow: UoW = manager.middleware_data["uow"]
    hamster: HamsterKombat = manager.middleware_data["hamster"]
    config: AppConfig = manager.middleware_data["config"]

    account_id: int = manager.start_data["account_id"]
    account: Optional[DBAccount] = await repo.accounts.get_one(
        DBAccount.config, account_id=account_id
    )
    account_proxy: Optional[DBAccountProxy] = await repo.proxies.get_one(
        config_id=account.config.id
    )

    proxy: str = manager.event.text

    proxy_data: Optional[ProxyData] = parse_proxy_from_string(proxy)
    if proxy_data is None:
        return await manager.event.answer(common_texts.INCORRECT_PROXY_DATA_TEXT)

    proxy_connector: ProxyConnector = ProxyConnector.from_url(proxy_data.url)
    if not await hamster.check_proxy(
        proxy_connector=proxy_connector, real_ip=config.common.server_ip
    ):
        return await manager.event.answer(common_texts.BAD_PROXY_DATA_TEXT)

    if account_proxy is None:
        account_proxy: DBAccountProxy = DBAccountProxy.create(
            config_id=account.config.id,
            protocol=proxy_data.protocol,
            host=proxy_data.host,
            port=proxy_data.port,
            username=proxy_data.username,
            password=proxy_data.password,
        )
    else:
        account_proxy.set_data(
            protocol=proxy_data.protocol,
            host=proxy_data.host,
            port=proxy_data.port,
            username=proxy_data.username,
            password=proxy_data.password,
            is_active=True,
        )

    await uow.add(account_proxy, commit=True)
    await manager.event.answer(common_texts.SUCCESS_TEXT)
    return await manager.switch_to(state=states.AccountConfigProxyDialog.INFO)


async def on_button_claim_daily_reward_all(
    _: CallbackQuery, __: Button, manager: DialogManager
):
    repo: Repository = manager.middleware_data["repo"]
    uow: UoW = manager.middleware_data["uow"]
    config: AppConfig = manager.middleware_data["config"]
    sched: AsyncScheduler = manager.middleware_data["sched"]
    hamster: HamsterKombat = manager.middleware_data["hamster"]
    user_id: int = manager.event.from_user.id
    task_id: str = "streak_days"

    _: asyncio.Task = asyncio.create_task(
        claim_daily_reward_thread(
            repo=repo,
            uow=uow,
            sched=sched,
            config=config,
            hamster=hamster,
            user_id=user_id,
            task_id=task_id,
        )
    )

    return await manager.event.answer("Ожидайте...")


async def claim_daily_reward_thread(
    repo: Repository,
    uow: UoW,
    sched: AsyncScheduler,
    config: AppConfig,
    hamster: HamsterKombat,
    user_id: int,
    task_id: str,
):
    async with Bot(
        config.common.bot_token.get_secret_value(),
        default=DefaultBotProperties(parse_mode="HTML"),
    ) as bot:
        accounts: list[Optional[DBAccount]] = await repo.accounts.get_all(
            DBAccount.config,
            user_id=user_id,
        )
        sum_reward: int = 0
        is_completed_rewards: int = 0
        is_not_completed_rewards: int = 0
        for account in accounts:
            await asyncio.sleep(random.randint(2, 6))
            account_proxy: Optional[DBAccountProxy] = await repo.proxies.get_one(
                config_id=account.config.id
            )
            proxy_connector: ProxyConnector = ProxyConnector.from_url(account_proxy.url)
            if not await hamster.check_proxy(
                proxy_connector=proxy_connector,
                real_ip=config.common.server_ip,
                response_timeout=account_proxy.timeout,
            ):
                await disable_account_proxy(
                    sched=sched, uow=uow, account=account, proxy=account_proxy
                )
                await bot.send_message(
                    chat_id=user_id,
                    text=f"""
❌ Не удалось подключиться к прокси для хомяка {account.full_name}.

Мы выключили автоматические функции для него, проверьте прокси и повторите попытку.
                    """,
                )
                continue

            hamster.set_proxy(proxy_connector=proxy_connector)

            try:
                task, hamster_data = await hamster.check_task(
                    bearer_token=account.token, task_id=task_id
                )
                if not task.is_completed:
                    is_not_completed_rewards += 1
                    continue

                is_completed_rewards += 1
                sum_reward += int(task.reward_coins)

                service.info(
                    "Task %s checked: %d | %s", task.type, account.id, account.full_name
                )
                await sync_tasks(repo=repo, uow=uow, account=account, hamster=hamster)
                await sync_account(uow=uow, account=account, hamster_data=hamster_data)
            except RequestError as error:
                service.error(error)
                await bot.send_message(
                    chat_id=user_id,
                    text=f"""
❌ Не удалось <b>синхронизировать аккаунт</b> с хомяком {account.full_name}.

Возможно, сервера <b>Hamster Kombat</b> плохо себя чувствуют, или <b>действие уже было выполнено</b>.
                    """,
                )
                continue

            await asyncio.sleep(random.randint(2, 6))

        return await bot.send_message(
            chat_id=user_id,
            text=f"""
✅ <b>Сбор наград</b> для <code>{len(accounts)}</code> <b>аккаунтов с хомяки</b> завершен.

<b>Кол-во удачных сборов:</b> <code>{is_completed_rewards}</code>
<b>Кол-во неудачных сборов (уже собрано):</b> <code>{is_not_completed_rewards}</code>
<b>Всего собрано монет:</b> <code>{sum_reward}</code>
            """,
        )
