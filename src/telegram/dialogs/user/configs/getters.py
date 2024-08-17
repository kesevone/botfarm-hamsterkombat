from typing import Any, Optional

from aiogram_dialog import DialogManager
from aiohttp_socks import ProxyConnector
from apscheduler import AsyncScheduler, Schedule
from babel.dates import format_datetime, get_timezone

from src.app_config import AppConfig
from src.database import Repository, UoW
from src.database.models import DBAccount, DBAccountConfig, DBAccountProxy
from src.enums import SchedulerActions, TaskIds
from src.utils.formatters import calculate_profit_upgrades
from src.hamster import (
    generate_schedule_id,
    HamsterKombat,
    HamsterUpgrade,
    process_schedule,
)


async def get_account_configs(dialog_manager: DialogManager, **_):
    repo: Repository = dialog_manager.middleware_data["repo"]
    user_id: str = dialog_manager.event.from_user.id
    accounts: Optional[list[DBAccount]] = await repo.accounts.get_all(
        DBAccount.config, user_id=user_id
    )

    return {
        "accounts": accounts,
    }


async def get_account_config(dialog_manager: DialogManager, **_):
    repo: Repository = dialog_manager.middleware_data["repo"]
    uow: UoW = dialog_manager.middleware_data["uow"]
    config: AppConfig = dialog_manager.middleware_data["config"]
    hamster: HamsterKombat = dialog_manager.middleware_data["hamster"]
    sched: AsyncScheduler = dialog_manager.middleware_data["sched"]
    account_id: int = dialog_manager.start_data["account_id"]
    account: DBAccount = await repo.accounts.get_one(
        DBAccount.config, DBAccount.upgrades, account_id=account_id
    )
    account_config: DBAccountConfig = account.config

    account_proxy: Optional[DBAccountProxy] = await repo.proxies.get_one(
        config_id=account.config.id
    )
    if account_proxy and account_proxy.is_active:
        proxy_connector: ProxyConnector = ProxyConnector.from_url(account_proxy.url)
        is_proxy_active: bool = await hamster.check_proxy(
            proxy_connector=proxy_connector,
            real_ip=config.common.server_ip,
            response_timeout=account_proxy.timeout,
        )
        if account_proxy.is_active != is_proxy_active:
            account_proxy.set_data(is_active=is_proxy_active)
            await uow.add(account_proxy, commit=True)

    autofarm_schedule: Optional[Schedule] = await process_schedule(
        sched=sched,
        action=SchedulerActions.GET,
        schedule_id=generate_schedule_id(
            task_id=TaskIds.AUTOFARM, account_id=account.id, user_id=account.user_id
        ),
        task_id=TaskIds.AUTOFARM,
    )
    autoupgrade_schedule: Optional[Schedule] = await process_schedule(
        sched=sched,
        action=SchedulerActions.GET,
        schedule_id=generate_schedule_id(
            task_id=TaskIds.AUTOUPGRADE, account_id=account.id, user_id=account.user_id
        ),
        task_id=TaskIds.AUTOUPGRADE,
    )
    autosync_schedule: Optional[Schedule] = await process_schedule(
        sched=sched,
        action=SchedulerActions.GET,
        schedule_id=generate_schedule_id(
            task_id=TaskIds.AUTOSYNC, account_id=account.id, user_id=account.user_id
        ),
        task_id=TaskIds.AUTOSYNC,
    )

    profit_upgrades: list[HamsterUpgrade] = calculate_profit_upgrades(
        account=account,
        upgrades=account.upgrades,
        sections=["Markets", "PR&Team", "Legal", "Specials"],
    )

    if autofarm_schedule is None:
        account_config.set_is_autofarm(is_autofarm=False)
        await uow.add(account_config, commit=True)

    if autoupgrade_schedule is None:
        account_config.set_is_autoupgrade(is_autoupgrade=False)
        await uow.add(account_config, commit=True)

    if autosync_schedule is None:
        account_config.set_is_autosync(is_autosync=False)
        await uow.add(account_config, commit=True)

    widget: Any = dialog_manager.find("autoupgrade_limit")
    if widget:
        await widget.set_checked(account_config.limit_percent)

    return {
        "account": account,
        "config": account_config,
        "is_autofarm": account_config.is_autofarm,
        "is_autofarm_notifications": account_config.is_autofarm_notifications,
        "is_autoupgrade": account_config.is_autoupgrade,
        "is_autoupgrade_notifications": account_config.is_autoupgrade_notifications,
        "is_autosync": account_config.is_autosync,
        "is_autosync_notifications": account_config.is_autosync_notifications,
        "next_run_autofarm": (
            format_datetime(
                autofarm_schedule.next_fire_time,
                "short",
                tzinfo=get_timezone("Europe/Moscow"),
                locale="ru_RU",
            )
            if autofarm_schedule
            else None
        ),
        "next_run_autoupgrade": (
            format_datetime(
                autoupgrade_schedule.next_fire_time,
                "short",
                tzinfo=get_timezone("Europe/Moscow"),
                locale="ru_RU",
            )
            if autoupgrade_schedule
            else None
        ),
        "next_run_autosync": (
            format_datetime(
                autosync_schedule.next_fire_time,
                "short",
                tzinfo=get_timezone("Europe/Moscow"),
                locale="ru_RU",
            )
            if autosync_schedule
            else None
        ),
        "profit_upgrades": profit_upgrades,
        "proxy": account_proxy,
        "is_proxy_active": account_proxy and account_proxy.is_active,
    }
