import asyncio
import os
import random
from datetime import datetime, timedelta
from typing import Any, Optional
from urllib.parse import unquote

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager, ShowMode
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button, ManagedRadio
from aiohttp_socks import ProxyConnector
from apscheduler import AsyncScheduler, Schedule
from apscheduler.triggers.interval import IntervalTrigger
from babel.dates import format_datetime, get_timezone
from pyrogram.raw import functions
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncEngine, AsyncSession

from src.app_config import AppConfig
from src.custom_pyrogram import CustomClient
from src.database import (
    Repository,
    SQLSessionContext,
    UoW,
)
from src.database.models import (
    DBAccount,
    DBAccountBoost,
    DBAccountCipher,
    DBAccountConfig,
    DBAccountProxy,
    DBAccountTask,
    DBAccountUpgrade,
    DBUser,
)
from src.enums import AuthType, SchedulerActions, TaskIds
from src.hamster import (
    add_schedule,
    AuthData,
    generate_schedule_id,
    HamsterBoosts,
    HamsterConfig,
    HamsterDailyCipher,
    HamsterDailyCombo,
    HamsterData,
    HamsterIPData,
    HamsterKombat,
    HamsterTasks,
    HamsterUpgrade,
    HamsterUpgrades,
    process_schedule,
    RequestError,
    UserData,
)
from src.telegram.dialogs import states
from src.telegram.dialogs.common import texts as common_texts
from src.utils.custom_jinja import CustomJinja
from src.utils.formatters import (
    calculate_autofarm_interval,
    calculate_autosync_interval,
    calculate_autoupgrade_interval,
    calculate_profit_upgrades,
    get_boost_description,
    get_boost_name,
)
from src.utils.loggers import service
from src.utils.parse_proxy import parse_proxy_from_string, ProxyData


async def create_account(
    repo: Repository,
    uow: UoW,
    user_data: UserData,
    auth_data: AuthData,
    proxy_data: ProxyData,
    user_id: int,
    hamster: HamsterKombat,
) -> Optional[
    tuple[
        DBAccount,
        DBAccountConfig,
        DBAccountCipher,
        DBAccountProxy,
        DBAccountUpgrade,
        DBAccountBoost,
        DBAccountTask,
        HamsterIPData,
    ]
]:
    hamster_config: HamsterConfig = await hamster.get_config(
        bearer_token=auth_data.auth_token
    )
    hamster_data: Optional[HamsterData] = await hamster.sync(
        bearer_token=auth_data.auth_token
    )

    daily_cipher: Optional[HamsterDailyCipher] = hamster_config.daily_cipher

    account: Optional[DBAccount] = await repo.accounts.get_one(account_id=user_data.id)
    if account is None:
        account: DBAccount = DBAccount.create(
            account_id=user_data.id,
            user_id=user_id,
            full_name=user_data.get_full_name(),
            token=auth_data.auth_token,
            username=user_data.username,
            referrals_count=hamster_data.referrals_count,
            level=hamster_data.level,
            total_coins=hamster_data.total_coins,
            balance_coins=hamster_data.balance_coins,
            available_taps=hamster_data.available_taps,
            max_taps=hamster_data.max_taps,
            earn_per_tap=hamster_data.earn_per_tap,
            earn_passive_per_sec=hamster_data.earn_passive_per_sec,
            earn_passive_per_hour=hamster_data.earn_passive_per_hour,
            last_passive_earn=hamster_data.last_passive_earn,
            taps_recover_per_sec=hamster_data.taps_recover_per_sec,
            updated_at=hamster_data.last_sync_update,
        )
    else:
        account.set_data(user_id=user_id, is_active=True)
    await uow.add(account, commit=True)

    account_config: Optional[DBAccountConfig] = await repo.configs.get_one(
        account_id=account.id
    )
    if account_config is None:
        account_config: DBAccountConfig = DBAccountConfig.create(
            account_id=account.id,
            autofarm_interval=calculate_autofarm_interval(
                available_taps=hamster_data.available_taps,
                max_taps=hamster_data.max_taps,
                taps_recover_per_sec=hamster_data.taps_recover_per_sec,
            ),
            autoupgrade_interval=calculate_autoupgrade_interval(),
            autosync_interval=calculate_autosync_interval(),
        )
    else:
        account_config.set_data(
            autofarm_interval=calculate_autofarm_interval(
                available_taps=hamster_data.available_taps,
                max_taps=hamster_data.max_taps,
                taps_recover_per_sec=hamster_data.taps_recover_per_sec,
            ),
            autoupgrade_interval=calculate_autoupgrade_interval(),
            autosync_interval=calculate_autosync_interval(),
            is_autosync=True,
        )
    await uow.add(account_config, commit=True)

    account_proxy: Optional[DBAccountProxy] = await repo.proxies.get_one(
        config_id=account_config.id
    )
    if account_proxy is None:
        account_proxy: DBAccountProxy = DBAccountProxy.create(
            config_id=account_config.id,
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
        )
    await uow.add(account_proxy, commit=True)

    account_cipher: Optional[DBAccountCipher] = await repo.ciphers.get_one(
        account_id=account.id
    )
    if account_cipher is None:
        account_cipher: DBAccountCipher = DBAccountCipher.create(
            account_id=account.id,
            bonus_coins=daily_cipher.bonus_coins,
            cipher=daily_cipher.cipher,
            is_claimed=daily_cipher.is_claimed,
            remain_seconds=daily_cipher.remain_seconds,
        )
    else:
        account_cipher.set_data(
            bonus_coins=daily_cipher.bonus_coins,
            cipher=daily_cipher.cipher,
            is_claimed=daily_cipher.is_claimed,
            remain_seconds=daily_cipher.remain_seconds,
        )

    await uow.add(account_cipher, commit=True)

    upgrades: list[DBAccountUpgrade] = await sync_upgrades(
        repo=repo, uow=uow, account=account, hamster=hamster
    )
    boosts: list[DBAccountBoost] = await sync_boosts(
        repo=repo, uow=uow, account=account, hamster=hamster
    )
    tasks: list[DBAccountTask] = await sync_tasks(
        repo=repo, uow=uow, account=account, hamster=hamster
    )
    ip_data: Optional[HamsterIPData] = await hamster.ip(
        bearer_token=auth_data.auth_token
    )

    return (
        account,
        account_config,
        account_cipher,
        account_proxy,
        upgrades,
        boosts,
        tasks,
        ip_data,
    )


async def parse_webapp_data_from_pyrogram_session(
    file_name: str, workdir: str, proxy: ProxyData
):
    async with CustomClient(
        file_name.replace(".session", ""),
        workdir=workdir,
        proxy={
            "scheme": proxy.protocol,
            "hostname": proxy.host,
            "port": proxy.port,
            "username": proxy.username,
            "password": proxy.password,
        },
    ) as app:
        app: CustomClient

        web_view = await app.invoke(
            functions.messages.RequestWebView(
                peer=await app.resolve_peer("hamster_kombat_bot"),
                bot=await app.resolve_peer("hamster_kombat_bot"),
                platform="android",
                from_bot_menu=False,
                url="https://hamsterkombat.io/clicker",
            )
        )

        auth_url = web_view.url
        webapp_data = unquote(
            string=auth_url.split("tgWebAppData=", maxsplit=1)[1].split(
                "&tgWebAppVersion", maxsplit=1
            )[0]
        )

        await app.stop()
        return webapp_data


async def disable_account_proxy(
    sched: AsyncScheduler, uow: UoW, account: DBAccount, proxy: DBAccountProxy
) -> None:
    account.config.set_is_autofarm(is_autofarm=False)
    account.config.set_is_autoupgrade(is_autoupgrade=False)
    account.config.set_is_autosync(is_autosync=False)

    await process_schedule(
        sched=sched,
        action=SchedulerActions.REMOVE,
        schedule_id=generate_schedule_id(
            task_id=TaskIds.AUTOFARM, account_id=account.id, user_id=account.user_id
        ),
    )
    await process_schedule(
        sched=sched,
        action=SchedulerActions.REMOVE,
        schedule_id=generate_schedule_id(
            task_id=TaskIds.AUTOUPGRADE, account_id=account.id, user_id=account.user_id
        ),
    )
    await process_schedule(
        sched=sched,
        action=SchedulerActions.REMOVE,
        schedule_id=generate_schedule_id(
            task_id=TaskIds.AUTOSYNC, account_id=account.id, user_id=account.user_id
        ),
    )

    if proxy is not None:
        proxy.set_data(is_active=False)
        await uow.add(proxy)

    await uow.add(account.config, commit=True)


async def buy_profit_upgrades(
    uow: UoW,
    account: DBAccount,
    upgrades: list[DBAccountUpgrade],
    hamster: HamsterKombat,
    sections: list[str],
) -> tuple[Optional[list[HamsterUpgrade]], DBAccount]:
    profit_upgrades: list[Optional[HamsterUpgrade]] = calculate_profit_upgrades(
        account=account,
        upgrades=upgrades,
        sections=sections,
    )

    success_upgrades: list[HamsterUpgrade] = []
    for upgrade in profit_upgrades:
        await asyncio.sleep(random.uniform(0.6, 1.2))
        if upgrade.price <= account.balance_coins:
            try:
                hamster_data: HamsterData = await hamster.buy_upgrade(
                    bearer_token=account.token, upgrade_id=upgrade.type
                )
            except RequestError as error:
                service.error(error)
                continue

            service.info(
                f"""
• Bought — {upgrade.type} | Price: {upgrade.price} | Profit per time: {upgrade.profit_per_time} h. | Level: {upgrade.level}
                        """
            )
            account: DBAccount = await sync_account(
                uow=uow,
                account=account,
                hamster_data=hamster_data,
            )
            success_upgrades.append(upgrade)
        await asyncio.sleep(random.uniform(0.6, 1.2))

    return success_upgrades, account


async def sync_boosts(
    repo: Repository,
    uow: UoW,
    account: DBAccount,
    hamster: Optional[HamsterKombat] = None,
    boosts: Optional[HamsterBoosts] = None,
) -> list[DBAccountBoost]:
    if not boosts:
        boosts: Optional[HamsterBoosts] = await hamster.get_boosts(
            bearer_token=account.token
        )

    synced_boosts: list[DBAccountBoost] = []
    for boost in boosts.boosts:
        account_boost: DBAccountBoost = await repo.boosts.get_one(
            boost_type=boost.type, account_id=account.id
        )

        if not account_boost:
            account_boost: DBAccountBoost = DBAccountBoost.create(
                boost_type=boost.type,
                name=get_boost_name(boost_type=boost.type),
                desc=get_boost_description(boost_type=boost.type),
                account_id=account.id,
                level=boost.level,
                price=boost.price,
                cooldown_seconds=boost.cooldown_seconds,
                earn_per_tap=boost.earn_per_tap,
                earn_per_tap_delta=boost.earn_per_tap_delta,
                max_taps=boost.max_taps,
                max_taps_delta=boost.max_taps_delta,
            )
        else:
            account_boost.set_data(
                level=boost.level,
                price=boost.price,
                cooldown_seconds=boost.cooldown_seconds,
                earn_per_tap=boost.earn_per_tap,
                max_taps=boost.max_taps,
            )

        await uow.add(account_boost)
        synced_boosts.append(account_boost)

    await uow.commit()
    service.info(
        "Sync HamsterBoosts from response, DBAccountBoost updated: %d | %s",
        account.id,
        account.full_name,
    )
    return synced_boosts


async def sync_upgrades(
    repo: Repository,
    uow: UoW,
    account: DBAccount,
    hamster: Optional[HamsterKombat] = None,
    upgrades: Optional[HamsterUpgrades] = None,
) -> list[DBAccountUpgrade]:
    if not upgrades:
        upgrades: Optional[HamsterUpgrades] = await hamster.get_upgrades(
            bearer_token=account.token
        )

    synced_upgrades: list[DBAccountUpgrade] = []
    for upgrade in upgrades.upgrades:
        account_upgrade: DBAccountUpgrade = await repo.upgrades.get_one(
            upgrade_type=upgrade.type, account_id=account.id
        )

        if not account_upgrade:
            account_upgrade: DBAccountUpgrade = DBAccountUpgrade.create(
                upgrade_type=upgrade.type,
                name=upgrade.name,
                section=upgrade.section,
                account_id=account.id,
                level=upgrade.level,
                price=upgrade.price,
                profit_per_hour=upgrade.profit_per_hour,
                cooldown_seconds=upgrade.cooldown_seconds,
                is_expired=upgrade.is_expired,
                is_active=upgrade.is_active,
            )
        else:
            account_upgrade.set_data(
                section=upgrade.section,
                level=upgrade.level,
                price=upgrade.price,
                profit_per_hour=upgrade.profit_per_hour,
                cooldown_seconds=upgrade.cooldown_seconds,
                is_expired=upgrade.is_expired,
                is_active=upgrade.is_active,
            )

            if upgrade.condition:
                account_condition: Optional[DBAccountUpgrade] = (
                    await repo.upgrades.get_one(
                        upgrade_type=upgrade.condition.upgrade_type,
                        account_id=account.id,
                    )
                )
                account_upgrade.set_data(
                    condition_id=account_condition.id, is_active=upgrade.is_active
                )

        synced_upgrades.append(account_upgrade)
        await uow.add(account_upgrade)

    await uow.commit()
    service.info(
        "Sync HamsterUpgrades from response, DBAccountUpgrade updated: %d | %s",
        account.id,
        account.full_name,
    )
    return synced_upgrades


async def sync_tasks(
    repo: Repository,
    uow: UoW,
    account: DBAccount,
    hamster: Optional[HamsterKombat] = None,
    tasks: Optional[HamsterTasks] = None,
) -> list[DBAccountTask]:
    if not tasks:
        tasks: Optional[HamsterTasks] = await hamster.get_tasks(
            bearer_token=account.token
        )

    synced_tasks: list[DBAccountTask] = []
    for task in tasks.tasks:
        account_task: Optional[DBAccountTask] = await repo.tasks.get_one(
            task_type=task.type, account_id=account.id
        )

        if account_task is None:
            account_task: DBAccountTask = DBAccountTask.create(
                task_type=task.type,
                account_id=account.id,
                days=task.days,
                reward_coins=task.reward_coins,
                is_completed=task.is_completed,
                completed_at=task.completed_at,
            )
        else:
            account_task.set_data(
                days=task.days,
                reward_coins=task.reward_coins,
                is_completed=task.is_completed,
                completed_at=task.completed_at,
            )

        synced_tasks.append(account_task)
        await uow.add(account_task)

    await uow.commit()
    service.info(
        "Sync HamsterTasks from response, DBAccountTask updated: %d | %s",
        account.id,
        account.full_name,
    )
    return synced_tasks


async def sync_account(
    uow: UoW,
    account: DBAccount,
    hamster: Optional[HamsterKombat] = None,
    hamster_data: Optional[HamsterData] = None,
    use_api_sync: Optional[bool] = False,
):
    if use_api_sync:
        hamster_data: Optional[HamsterData] = await hamster.sync(
            bearer_token=account.token
        )

    account.set_data(
        referrals_count=hamster_data.referrals_count,
        level=hamster_data.level,
        total_coins=hamster_data.total_coins,
        balance_coins=hamster_data.balance_coins,
        available_taps=hamster_data.available_taps,
        max_taps=hamster_data.max_taps,
        earn_per_tap=hamster_data.earn_per_tap,
        earn_passive_per_sec=hamster_data.earn_passive_per_sec,
        earn_passive_per_hour=hamster_data.earn_passive_per_hour,
        last_passive_earn=hamster_data.last_passive_earn,
        taps_recover_per_sec=hamster_data.taps_recover_per_sec,
        updated_at=hamster_data.last_sync_update,
    )
    await uow.add(account, account.config, commit=True)

    service.info(
        "Sync account from response, HamsterData updated: %d | %s",
        account.id,
        account.full_name,
    )
    return account


async def full_sync(
    repo: Repository,
    uow: UoW,
    account: DBAccount,
    hamster: HamsterKombat,
    hamster_data: Optional[HamsterData] = None,
    use_api_sync: Optional[bool] = False,
) -> DBAccount:

    if use_api_sync:
        hamster_data: Optional[HamsterData] = await hamster.sync(
            bearer_token=account.token
        )

    if hamster_data is not None:
        account.set_data(
            referrals_count=hamster_data.referrals_count,
            level=hamster_data.level,
            total_coins=hamster_data.total_coins,
            balance_coins=hamster_data.balance_coins,
            available_taps=hamster_data.available_taps,
            max_taps=hamster_data.max_taps,
            earn_per_tap=hamster_data.earn_per_tap,
            earn_passive_per_sec=hamster_data.earn_passive_per_sec,
            earn_passive_per_hour=hamster_data.earn_passive_per_hour,
            last_passive_earn=hamster_data.last_passive_earn,
            taps_recover_per_sec=hamster_data.taps_recover_per_sec,
            updated_at=hamster_data.last_sync_update,
        )

    account.config.set_autofarm_interval(
        autofarm_interval=calculate_autofarm_interval(),
    )
    account.config.set_autoupgrade_interval(
        autoupgrade_interval=calculate_autoupgrade_interval(),
    )
    account.config.set_autosync_interval(
        autosync_interval=calculate_autosync_interval(),
    )

    cipher: Optional[DBAccountCipher] = await repo.ciphers.get_one(
        account_id=account.id
    )

    hamster_config: HamsterConfig = await hamster.get_config(bearer_token=account.token)
    daily_cipher: Optional[HamsterDailyCipher] = hamster_config.daily_cipher

    if cipher is None:
        cipher: DBAccountCipher = DBAccountCipher.create(
            account_id=account.id,
            bonus_coins=daily_cipher.bonus_coins,
            cipher=daily_cipher.cipher,
            is_claimed=daily_cipher.is_claimed,
            remain_seconds=daily_cipher.remain_seconds,
        )
    else:
        cipher.set_data(
            bonus_coins=daily_cipher.bonus_coins,
            cipher=daily_cipher.cipher,
            is_claimed=daily_cipher.is_claimed,
            remain_seconds=daily_cipher.remain_seconds,
        )

    await uow.add(account, cipher, commit=True)

    boosts: Optional[HamsterBoosts] = await hamster.get_boosts(
        bearer_token=account.token
    )
    upgrades: Optional[HamsterUpgrades] = await hamster.get_upgrades(
        bearer_token=account.token
    )
    tasks: Optional[HamsterTasks] = await hamster.get_tasks(bearer_token=account.token)

    for boost in boosts.boosts:
        account_boost: Optional[DBAccountBoost] = await repo.boosts.get_one(
            boost_type=boost.type, account_id=account.id
        )

        if account_boost is None:
            account_boost: DBAccountBoost = DBAccountBoost.create(
                boost_type=boost.type,
                name=get_boost_name(boost_type=boost.type),
                desc=get_boost_description(boost_type=boost.type),
                account_id=account.id,
                level=boost.level,
                price=boost.price,
                cooldown_seconds=boost.cooldown_seconds,
                earn_per_tap=boost.earn_per_tap,
                earn_per_tap_delta=boost.earn_per_tap_delta,
                max_taps=boost.max_taps,
                max_taps_delta=boost.max_taps_delta,
            )
        else:
            account_boost.set_data(
                level=boost.level,
                price=boost.price,
                cooldown_seconds=boost.cooldown_seconds,
                earn_per_tap=boost.earn_per_tap,
                max_taps=boost.max_taps,
            )

        await uow.add(account_boost)

    for upgrade in upgrades.upgrades:
        account_upgrade: Optional[DBAccountUpgrade] = await repo.upgrades.get_one(
            upgrade_type=upgrade.type, account_id=account.id
        )

        if account_upgrade is None:
            account_upgrade: DBAccountUpgrade = DBAccountUpgrade.create(
                upgrade_type=upgrade.type,
                name=upgrade.name,
                section=upgrade.section,
                account_id=account.id,
                level=upgrade.level,
                price=upgrade.price,
                profit_per_hour=upgrade.profit_per_hour,
                cooldown_seconds=upgrade.cooldown_seconds,
                is_expired=upgrade.is_expired,
                is_active=upgrade.is_active,
            )
        else:
            if upgrade.condition:
                account_condition: Optional[DBAccountUpgrade] = (
                    await repo.upgrades.get_one(
                        upgrade_type=upgrade.condition.upgrade_type,
                        account_id=account.id,
                    )
                )
                if account_condition:
                    account_upgrade.set_data(condition_id=account_condition.id)

            account_upgrade.set_data(
                section=upgrade.section,
                level=upgrade.level,
                price=upgrade.price,
                profit_per_hour=upgrade.profit_per_hour,
                cooldown_seconds=upgrade.cooldown_seconds,
                is_expired=upgrade.is_expired,
                is_active=upgrade.is_active,
            )

        await uow.add(account_upgrade)

    for task in tasks.tasks:
        account_task: Optional[DBAccountTask] = await repo.tasks.get_one(
            task_type=task.type, account_id=account.id
        )

        if account_task is None:
            account_task: DBAccountTask = DBAccountTask.create(
                task_type=task.type,
                account_id=account.id,
                days=task.days,
                reward_coins=task.reward_coins,
                periodicity=task.periodicity,
                is_completed=task.is_completed,
                completed_at=task.completed_at,
            )
        else:
            account_task.set_data(
                days=task.days,
                reward_coins=task.reward_coins,
                periodicity=task.periodicity,
                is_completed=task.is_completed,
                completedAt=task.completed_at,
            )

        await uow.add(account_task)

    await uow.commit()
    service.info(
        "FULL sync account from response, HamsterData updated: %d | %s",
        account.id,
        account.full_name,
    )
    return account


async def on_start_account_creator_dialog(
    _: CallbackQuery, __: Button, manager: DialogManager
):
    return await manager.start(states.AccountCreatorDialog.SELECT_AUTH_TYPE)


async def on_switch_to_input_proxy_data(
    _: CallbackQuery, widget: Button, manager: DialogManager
):
    auth_type: AuthType = widget.widget_id
    manager.dialog_data["auth_type"] = auth_type
    return await manager.switch_to(states.AccountCreatorDialog.INPUT_PROXY_DATA)


async def on_switch_to_auth_type(_: Message, __: MessageInput, manager: DialogManager):
    hamster: HamsterKombat = manager.middleware_data["hamster"]
    config: AppConfig = manager.middleware_data["config"]

    proxy: str = manager.event.text

    proxy_data: Optional[ProxyData] = parse_proxy_from_string(proxy)
    if proxy_data is None:
        return await manager.event.answer(common_texts.INCORRECT_PROXY_DATA_TEXT)

    proxy_connector: ProxyConnector = ProxyConnector.from_url(proxy_data.url)
    if not await hamster.check_proxy(
        proxy_connector=proxy_connector,
        real_ip=config.common.server_ip,
    ):
        return await manager.event.answer(common_texts.BAD_PROXY_DATA_TEXT)

    manager.dialog_data["proxy_url"] = proxy_data.url
    auth_type: AuthType = manager.dialog_data["auth_type"]

    if auth_type == AuthType.BEARER:
        return await manager.switch_to(states.AccountCreatorDialog.BEARER_TOKEN)
    if auth_type == AuthType.WEBAPP_DATA:
        return await manager.switch_to(states.AccountCreatorDialog.WEBAPP_DATA)
    if auth_type == AuthType.SESSION:
        return await manager.switch_to(states.AccountCreatorDialog.SESSION)

    return await manager.event.answer(common_texts.SOMETHING_WENT_WRONG_TEXT)


async def on_auth_with_webapp_or_bearer_data(
    _: Message, __: MessageInput, manager: DialogManager
):
    repo: Repository = manager.middleware_data["repo"]
    uow: UoW = manager.middleware_data["uow"]
    sched: AsyncScheduler = manager.middleware_data["sched"]
    hamster: HamsterKombat = manager.middleware_data["hamster"]
    auth_type: AuthType = manager.dialog_data["auth_type"]

    proxy_url: str = manager.dialog_data["proxy_url"]
    proxy_data: Optional[ProxyData] = parse_proxy_from_string(proxy_url)
    proxy_connector: ProxyConnector = ProxyConnector.from_url(proxy_url)
    hamster.set_proxy(proxy_connector=proxy_connector)

    user_id: int = manager.event.from_user.id
    data: str = manager.event.text

    try:
        if auth_type == AuthType.WEBAPP_DATA:
            if not data.startswith("query_id="):
                return await manager.event.answer(
                    common_texts.INCORRECT_WEBAPP_DATA_TEXT
                )

            auth_data: Optional[AuthData] = await hamster.auth_webapp(webapp_data=data)
        else:
            auth_data: AuthData = AuthData(authToken=data)

        user_data: Optional[UserData] = await hamster.auth_telegram(
            bearer_token=auth_data.auth_token,
        )
    except RequestError as error:
        service.error(error)
        return await manager.event.answer(common_texts.UNKNOWN_ERROR_REQUEST_TEXT)

    account: Optional[DBAccount] = await repo.accounts.get_one(account_id=user_data.id)
    if account:
        if account.user_id:
            return await manager.event.answer(
                f"""
⚠️ Хомяк <b>{account.full_name}</b> (<code>{account.id}</code>) уже привязан к <b>другому</b> аккаунту.
                """
            )
        else:
            try:
                data: tuple[
                    DBAccount,
                    DBAccountConfig,
                    DBAccountCipher,
                    DBAccountUpgrade,
                    DBAccountBoost,
                    DBAccountTask,
                    HamsterIPData,
                ] = await create_account(
                    repo=repo,
                    uow=uow,
                    user_data=user_data,
                    auth_data=auth_data,
                    proxy_data=proxy_data,
                    user_id=user_id,
                    hamster=hamster,
                )
            except RequestError as error:
                service.error(error)
                await uow.rollback()
                return await manager.event.answer(
                    common_texts.UNKNOWN_ERROR_REQUEST_TEXT
                )

            account: DBAccount = data[0]
            config: DBAccountConfig = data[1]

            await add_schedule(
                sched=sched,
                trigger=IntervalTrigger(seconds=config.autosync_interval),
                schedule_id=generate_schedule_id(
                    task_id=TaskIds.AUTOSYNC,
                    account_id=account.id,
                    user_id=account.user_id,
                ),
                task_id=TaskIds.AUTOSYNC,
                account_id=account.id,
            )

            service.info(
                "Account linked: %d | %s",
                account.id,
                account.full_name,
            )
    else:
        try:
            data: tuple[
                DBAccount,
                DBAccountConfig,
                DBAccountCipher,
                DBAccountUpgrade,
                DBAccountBoost,
                DBAccountTask,
                HamsterIPData,
            ] = await create_account(
                repo=repo,
                uow=uow,
                user_data=user_data,
                auth_data=auth_data,
                proxy_data=proxy_data,
                user_id=user_id,
                hamster=hamster,
            )
        except RequestError as error:
            service.error(error)
            await uow.rollback()
            return await manager.event.answer(common_texts.UNKNOWN_ERROR_REQUEST_TEXT)

        account: DBAccount = data[0]
        config: DBAccountConfig = data[1]

        service.info(
            "Account created: %d | %s",
            account.id,
            account.full_name,
        )

        await add_schedule(
            sched=sched,
            trigger=IntervalTrigger(seconds=config.autosync_interval),
            schedule_id=generate_schedule_id(
                task_id=TaskIds.AUTOSYNC,
                account_id=account.id,
                user_id=account.user_id,
            ),
            task_id=TaskIds.AUTOSYNC,
            account_id=account.id,
        )

    return await manager.done(show_mode=ShowMode.DELETE_AND_SEND)


async def on_auth_with_session(_: Message, __: MessageInput, manager: DialogManager):
    repo: Repository = manager.middleware_data["repo"]
    config: AppConfig = manager.middleware_data["config"]
    uow: UoW = manager.middleware_data["uow"]
    sched: AsyncScheduler = manager.middleware_data["sched"]
    hamster: HamsterKombat = manager.middleware_data["hamster"]

    user_id: int = manager.event.from_user.id
    file_id: str = manager.event.document.file_id
    file_name: str = manager.event.document.file_name
    workdir: str = config.common.sessions_path

    proxy_url: str = manager.dialog_data["proxy_url"]
    proxy_data: Optional[ProxyData] = parse_proxy_from_string(proxy_url)
    proxy_connector: ProxyConnector = ProxyConnector.from_url(proxy_url)
    hamster.set_proxy(proxy_connector=proxy_connector)

    await manager.event.bot.download(file_id, destination=workdir + file_name)

    try:
        webapp_data: str = await parse_webapp_data_from_pyrogram_session(
            file_name=file_name, workdir=workdir, proxy=proxy_data
        )
    except AttributeError as e:
        service.error(e)
        return await manager.event.answer(common_texts.SESSION_NOT_REGISTERED_TEXT)
    except Exception as e:
        service.error(e)
        return await manager.event.answer(common_texts.SOMETHING_WENT_WRONG_TEXT)
    finally:
        os.remove(workdir + file_name)

    try:
        auth_data: Optional[AuthData] = await hamster.auth_webapp(
            webapp_data=webapp_data
        )
        user_data: Optional[UserData] = await hamster.auth_telegram(
            bearer_token=auth_data.auth_token,
        )
    except RequestError as error:
        service.error(error)
        return await manager.event.answer(common_texts.UNKNOWN_ERROR_REQUEST_TEXT)

    account: Optional[DBAccount] = await repo.accounts.get_one(account_id=user_data.id)
    if account:
        if account.user_id:
            return await manager.event.answer(
                f"""
⚠️ Хомяк <b>{account.full_name}</b> (<code>{account.id}</code>) уже привязан к <b>другому</b> аккаунту.
                """
            )
        else:
            try:
                data: tuple[
                    DBAccount,
                    DBAccountConfig,
                    DBAccountCipher,
                    DBAccountUpgrade,
                    DBAccountBoost,
                    DBAccountTask,
                    HamsterIPData,
                ] = await create_account(
                    repo=repo,
                    uow=uow,
                    user_data=user_data,
                    auth_data=auth_data,
                    proxy_data=proxy_data,
                    user_id=user_id,
                    hamster=hamster,
                )
            except RequestError as error:
                service.error(error)
                await uow.rollback()
                return await manager.event.answer(
                    common_texts.UNKNOWN_ERROR_REQUEST_TEXT
                )

            account: DBAccount = data[0]
            config: DBAccountConfig = data[1]

            await add_schedule(
                sched=sched,
                trigger=IntervalTrigger(seconds=config.autosync_interval),
                schedule_id=generate_schedule_id(
                    task_id=TaskIds.AUTOSYNC,
                    account_id=account.id,
                    user_id=account.user_id,
                ),
                task_id=TaskIds.AUTOSYNC,
                account_id=account.id,
            )

            service.info(
                "Account linked: %d | %s",
                account.id,
                account.full_name,
            )
    else:
        try:
            data: tuple[
                DBAccount,
                DBAccountConfig,
                DBAccountCipher,
                DBAccountUpgrade,
                DBAccountBoost,
                DBAccountTask,
                HamsterIPData,
            ] = await create_account(
                repo=repo,
                uow=uow,
                user_data=user_data,
                auth_data=auth_data,
                proxy_data=proxy_data,
                user_id=user_id,
                hamster=hamster,
            )
            account: DBAccount = data[0]
            config: DBAccountConfig = data[1]

            service.info(
                "Account created: %d | %s",
                account.id,
                account.full_name,
            )
        except RequestError as error:
            service.error(error)
            await uow.rollback()
            return await manager.event.answer(common_texts.UNKNOWN_ERROR_REQUEST_TEXT)

        await add_schedule(
            sched=sched,
            trigger=IntervalTrigger(seconds=config.autosync_interval),
            schedule_id=generate_schedule_id(
                task_id=TaskIds.AUTOSYNC,
                account_id=account.id,
                user_id=account.user_id,
            ),
            task_id=TaskIds.AUTOSYNC,
            account_id=account.id,
        )

    return await manager.done(show_mode=ShowMode.DELETE_AND_SEND)


async def on_select_account_by_id(
    _: CallbackQuery, __: Button, manager: DialogManager, account_id: int
):
    repo: Repository = manager.middleware_data["repo"]
    account: Optional[DBAccount] = await repo.accounts.get_one(account_id=account_id)
    if account is None:
        return await manager.event.answer(common_texts.ACCOUNT_NOT_FOUND_TEXT)

    data: dict[str, Any] = {"account_id": account.id}
    return await manager.start(states.AccountDialog.INFO, data=data)


async def on_button_tap(_: CallbackQuery, __: Button, manager: DialogManager):
    repo: Repository = manager.middleware_data["repo"]
    uow: UoW = manager.middleware_data["uow"]
    config: AppConfig = manager.middleware_data["config"]
    sched: AsyncScheduler = manager.middleware_data["sched"]
    hamster: HamsterKombat = manager.middleware_data["hamster"]
    account_id: int = manager.start_data["account_id"]
    account: Optional[DBAccount] = await repo.accounts.get_one(
        DBAccount.config,
        account_id=account_id,
    )

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
        return await manager.event.answer(
            f"""
    ❌ Не удалось подключиться к прокси для хомяка {account.full_name}.

    Мы выключили автоматические функции для него, проверьте прокси и повторите попытку.
            """,
            show_alert=True,
        )

    hamster.set_proxy(proxy_connector=proxy_connector)

    energy: int = account.available_taps // account.earn_per_tap
    try:
        hamster_data: Optional[HamsterData] = await hamster.tap(
            bearer_token=account.token,
            available_taps=account.available_taps,
            count=(energy // 1.5) + random.randint(11, 34),
        )
        service.info("Tapped on account: %d | %s", account.id, account.full_name)
        await sync_account(
            uow=uow,
            account=account,
            hamster_data=hamster_data,
        )
    except RequestError as error:
        service.error(error)
        return await manager.event.answer(common_texts.CANNOT_SYNC_ACCOUNT_TEXT)


async def on_claim_daily_cipher(_: CallbackQuery, __: Button, manager: DialogManager):
    repo: Repository = manager.middleware_data["repo"]
    uow: UoW = manager.middleware_data["uow"]
    config: AppConfig = manager.middleware_data["config"]
    sched: AsyncScheduler = manager.middleware_data["sched"]
    hamster: HamsterKombat = manager.middleware_data["hamster"]

    account_id: int = manager.start_data["account_id"]
    account: Optional[DBAccount] = await repo.accounts.get_one(
        DBAccount.config,
        account_id=account_id,
    )
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
        return await manager.event.answer(
            f"""
❌ Не удалось подключиться к прокси для хомяка {account.full_name}.

Мы выключили автоматические функции для него, проверьте прокси и повторите попытку.
            """,
            show_alert=True,
        )

    hamster.set_proxy(proxy_connector=proxy_connector)

    cipher: Optional[DBAccountCipher] = await repo.ciphers.get_one(
        account_id=account.id
    )
    if cipher is None:
        hamster_config: HamsterConfig = await hamster.get_config(
            bearer_token=account.token
        )
        daily_cipher: HamsterDailyCipher = hamster_config.daily_cipher
        cipher: DBAccountCipher = DBAccountCipher.create(
            account_id=account.id,
            bonus_coins=daily_cipher.bonus_coins,
            cipher=daily_cipher,
            is_claimed=daily_cipher.is_claimed,
            remain_seconds=daily_cipher.remain_seconds,
        )

    if cipher.is_claimed:
        return await manager.event.answer(
            common_texts.ALREADY_CLAIMED_DAILY_CIPHER_TEXT
        )

    try:
        hamster_data, daily_cipher = await hamster.claim_daily_cipher(
            bearer_token=account.token, cipher=cipher.cipher
        )
        cipher.set_data(is_claimed=daily_cipher.is_claimed)
        await uow.add(cipher, commit=True)
        await sync_account(uow=uow, account=account, hamster_data=hamster_data)

        service.info("Daily cipher claimed: %d | %s", account.id, account.full_name)
    except RequestError as error:
        service.error(error)
        return await manager.event.answer(common_texts.CANNOT_CLAIM_DAILY_CIPHER_TEXT)

    return await manager.event.answer(common_texts.SUCCESS_TEXT)


async def on_claim_daily_combo(_: CallbackQuery, __: Button, manager: DialogManager):
    repo: Repository = manager.middleware_data["repo"]
    uow: UoW = manager.middleware_data["uow"]
    config: AppConfig = manager.middleware_data["config"]
    sched: AsyncScheduler = manager.middleware_data["sched"]
    hamster: HamsterKombat = manager.middleware_data["hamster"]
    account_id: int = manager.start_data["account_id"]
    account: Optional[DBAccount] = await repo.accounts.get_one(
        DBAccount.config,
        account_id=account_id,
    )

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
        return await manager.event.answer(
            f"""
❌ Не удалось подключиться к прокси для хомяка {account.full_name}.

Мы выключили автоматические функции для него, проверьте прокси и повторите попытку.
            """,
            show_alert=True,
        )

    hamster.set_proxy(proxy_connector=proxy_connector)
    upgrades: Optional[HamsterUpgrades] = await hamster.get_upgrades(
        bearer_token=account.token
    )

    if upgrades.daily_combo.is_claimed:
        return await manager.event.answer(common_texts.ALREADY_CLAIMED_DAILY_COMBO_TEXT)

    actual_combos: Optional[HamsterDailyCombo] = await hamster.get_actual_combos()
    if (
        not set(actual_combos.upgrade_ids).issubset(
            set(upgrades.daily_combo.upgrade_ids)
        )
        and actual_combos.actual_date
        and int(actual_combos.actual_date.split("-")[0]) == datetime.now().date().day
        and int(actual_combos.actual_date.split("-")[1]) == datetime.now().date().month
    ):
        missing_upgrade_ids = set(actual_combos.upgrade_ids) - set(
            upgrades.daily_combo.upgrade_ids
        )
        try:
            last_hamster_data: Optional[HamsterData] = None
            for missin_upgrade in missing_upgrade_ids:
                upgrade: Optional[DBAccountUpgrade] = await repo.upgrades.get_one(
                    account_id=account.id,
                    upgrade_type=missin_upgrade,
                )
                if upgrade is None or not upgrade.is_active or upgrade.is_expired:
                    return await manager.event.answer(
                        """
Не удалось найти апгрейд в базе, или он не доступен/истечён.
                        """
                    )

                await asyncio.sleep(random.uniform(0.6, 1.2))
                hamster_data: Optional[HamsterData] = await hamster.buy_upgrade(
                    bearer_token=account.token, upgrade_id=missin_upgrade
                )
                last_hamster_data = hamster_data
                await asyncio.sleep(random.uniform(0.6, 1.2))

            await sync_account(uow=uow, account=account, hamster_data=last_hamster_data)

            service.info(
                "Bought missing upgrades: %d | %s", account.id, account.full_name
            )
        except RequestError as error:
            service.error(error)
            return await manager.event.answer(
                common_texts.CANNOT_CLAIM_DAILY_COMBO_TEXT
            )

    try:
        hamster_data: Optional[HamsterData] = await hamster.claim_daily_combo(
            bearer_token=account.token
        )

        await sync_account(uow=uow, account=account, hamster_data=hamster_data)

        service.info("Daily combo claimed: %d | %s", account.id, account.full_name)
    except RequestError as error:
        service.error(error)
        return await manager.event.answer(common_texts.CANNOT_CLAIM_DAILY_COMBO_TEXT)

    return await manager.event.answer(common_texts.SUCCESS_TEXT)


async def on_claim_daily_task(_: CallbackQuery, __: Button, manager: DialogManager):
    repo: Repository = manager.middleware_data["repo"]
    uow: UoW = manager.middleware_data["uow"]
    config: AppConfig = manager.middleware_data["config"]
    sched: AsyncScheduler = manager.middleware_data["sched"]
    hamster: HamsterKombat = manager.middleware_data["hamster"]

    account_id: int = manager.start_data["account_id"]
    task_id: str = manager.start_data["task_id"]

    account: Optional[DBAccount] = await repo.accounts.get_one(
        DBAccount.config,
        account_id=account_id,
    )
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
        return await manager.event.answer(
            f"""
❌ Не удалось подключиться к прокси для хомяка {account.full_name}.

Мы выключили автоматические функции для него, проверьте прокси и повторите попытку.
            """,
            show_alert=True,
        )

    hamster.set_proxy(proxy_connector=proxy_connector)

    try:
        task, hamster_data = await hamster.check_task(
            bearer_token=account.token, task_id=task_id
        )
        service.info(
            "Task %s checked: %d | %s", task.type, account.id, account.full_name
        )
        await sync_tasks(repo=repo, uow=uow, account=account, hamster=hamster)
        await sync_account(uow=uow, account=account, hamster_data=hamster_data)
    except RequestError as error:
        service.error(error)
        return await manager.event.answer(common_texts.CANNOT_SYNC_ACCOUNT_TEXT)

    return await manager.event.answer(common_texts.SUCCESS_TEXT)


async def on_button_sync_data(_: CallbackQuery, __: Button, manager: DialogManager):
    repo: Repository = manager.middleware_data["repo"]
    uow: UoW = manager.middleware_data["uow"]
    config: AppConfig = manager.middleware_data["config"]
    sched: AsyncScheduler = manager.middleware_data["sched"]
    hamster: HamsterKombat = manager.middleware_data["hamster"]

    account_id: int = manager.start_data["account_id"]

    account: Optional[DBAccount] = await repo.accounts.get_one(
        DBAccount.config, account_id=account_id
    )
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
        return await manager.event.answer(
            f"""
❌ Не удалось подключиться к прокси для хомяка {account.full_name}.

Мы выключили автоматические функции для него, проверьте прокси и повторите попытку.
            """,
            show_alert=True,
        )

    hamster.set_proxy(proxy_connector=proxy_connector)

    try:
        await full_sync(
            repo=repo, uow=uow, account=account, hamster=hamster, use_api_sync=True
        )
    except RequestError as error:
        service.error(error)
        return await manager.event.answer(common_texts.CANNOT_SYNC_ACCOUNT_TEXT)

    # await add_schedule(
    #     sched=sched,
    #     trigger=IntervalTrigger(seconds=account.config.autofarm_interval),
    #     schedule_id=generate_schedule_id(
    #         task_id=TaskIds.AUTOFARM, account_id=account.id, user_id=account.user_id
    #     ),
    #     task_id=TaskIds.AUTOFARM,
    #     account_id=account.id,
    # )
    # await add_schedule(
    #     sched=sched,
    #     trigger=IntervalTrigger(seconds=account.config.autoupgrade_interval),
    #     schedule_id=generate_schedule_id(
    #         task_id=TaskIds.AUTOUPGRADE, account_id=account.id, user_id=account.user_id
    #     ),
    #     task_id=TaskIds.AUTOUPGRADE,
    #     account_id=account.id,
    # )
    # await add_schedule(
    #     sched=sched,
    #     trigger=IntervalTrigger(seconds=account.config.autosync_interval),
    #     schedule_id=generate_schedule_id(
    #         task_id=TaskIds.AUTOSYNC, account_id=account.id, user_id=account.user_id
    #     ),
    #     task_id=TaskIds.AUTOSYNC,
    #     account_id=account.id
    # )

    return await manager.event.answer(common_texts.SUCCESS_TEXT)


async def on_button_sync_data_all(_: CallbackQuery, __: Button, manager: DialogManager):
    repo: Repository = manager.middleware_data["repo"]
    sched: AsyncScheduler = manager.middleware_data["sched"]
    uow: UoW = manager.middleware_data["uow"]
    hamster: HamsterKombat = manager.middleware_data["hamster"]

    user_id: int = manager.event.from_user.id

    accounts: list[Optional[DBAccount]] = await repo.accounts.get_all(
        DBAccount.config, user_id=user_id
    )
    for account in accounts:
        try:
            account: DBAccount = await full_sync(
                repo=repo, uow=uow, account=account, hamster=hamster
            )
        except RequestError as error:
            service.error(error)
            return await manager.event.answer(common_texts.CANNOT_SYNC_ACCOUNT_TEXT)

        await process_schedule(
            sched=sched,
            schedule_id=generate_schedule_id(
                task_id=TaskIds.AUTOFARM,
                account_id=account.id,
                user_id=account.user_id,
            ),
            task_id=TaskIds.AUTOFARM,
            action=SchedulerActions.RESCHEDULE,
            trigger=IntervalTrigger(seconds=account.config.autofarm_interval),
            account_id=account.id,
        )

    return await manager.event.answer(common_texts.SUCCESS_TEXT)


async def handle_autosync(
    account_id: int,
    bot: Bot,
    hamster: HamsterKombat,
    config: AppConfig,
    session: async_sessionmaker[AsyncSession],
    engine: AsyncEngine,
    **_,
) -> None:
    async with SQLSessionContext(session_pool=session) as (repo, uow):
        account: Optional[DBAccount] = await repo.accounts.get_one(
            DBAccount.config, account_id=account_id
        )

        account_proxy: Optional[DBAccountProxy] = await repo.proxies.get_one(
            config_id=account.config.id
        )
        async with config.postgres.build_scheduler(engine=engine) as sched:
            if account_proxy is None:
                await disable_account_proxy(
                    sched=sched, uow=uow, account=account, proxy=account_proxy
                )
                return await bot.send_message(
                    chat_id=account.user_id,
                    text=f"""
❌ Не удалось <b>подключиться к прокси</b> для хомяка {account.full_name}.

Мы выключили <b>автоматические функции для него</b>, проверьте прокси и повторите попытку.
                        """,
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
                return await bot.send_message(
                    chat_id=account.user_id,
                    text=f"""
❌ Не удалось <b>подключиться к прокси</b> для хомяка {account.full_name}.

Мы выключили <b>автоматические функции для него</b>, проверьте прокси и повторите попытку.
                        """,
                )

            hamster.set_proxy(proxy_connector=proxy_connector)

            try:
                account: DBAccount = await full_sync(
                    repo=repo,
                    uow=uow,
                    account=account,
                    hamster=hamster,
                    use_api_sync=True,
                )
            except RequestError as error:
                await bot.send_message(
                    chat_id=account.user_id,
                    text=f"❌ Ошибка <b>авто-синхронизации</b>, аккаунт: {account.full_name} (<code>{account.id}</code>).",
                )
                return service.error(error)

            if account.config.is_autosync_notifications:
                schedule: Optional[Schedule] = await process_schedule(
                    sched=sched,
                    schedule_id=generate_schedule_id(
                        task_id=TaskIds.AUTOSYNC,
                        account_id=account_id,
                        user_id=account.user_id,
                    ),
                    task_id=TaskIds.AUTOSYNC,
                    action=SchedulerActions.GET,
                )

                await bot.send_message(
                    chat_id=account.user_id,
                    text=await CustomJinja(
                        """
👍 Аккаунт {{ account.full_name }} (<code>{{ account.id }}</code>) <b>успешно синхронизирован</b> с базой данных.

🔄 <b>Авто-синхронизация:</b>
{% if next_run_autosync %}
└ <b>Следующий запуск:</b> <code>{{ next_run_autosync }}</code>
{% else %}
└ ⚠️ Не удалось получить <b>дату и время следующего запуска</b>.
{% endif %}
                        """,
                        next_run_autosync=(
                            format_datetime(
                                schedule.next_fire_time,
                                "short",
                                tzinfo=get_timezone("Europe/Moscow"),
                                locale="ru_RU",
                            )
                            if schedule
                            else None
                        ),
                        account=account,
                    ).render(),
                )


async def handle_autoupgrade(
    account_id: int,
    bot: Bot,
    hamster: HamsterKombat,
    config: AppConfig,
    session: async_sessionmaker[AsyncSession],
    engine: AsyncEngine,
    **_,
) -> None:
    async with SQLSessionContext(session_pool=session) as (repo, uow):
        account: Optional[DBAccount] = await repo.accounts.get_one(
            DBAccount.upgrades, DBAccount.config, account_id=account_id
        )

        account_proxy: Optional[DBAccountProxy] = await repo.proxies.get_one(
            config_id=account.config.id
        )

        async with config.postgres.build_scheduler(engine=engine) as sched:
            if account_proxy is None:
                await disable_account_proxy(
                    sched=sched, uow=uow, account=account, proxy=account_proxy
                )
                return await bot.send_message(
                    chat_id=account.user_id,
                    text=f"""
❌ Не удалось <b>подключиться к прокси</b> для хомяка {account.full_name}.

Мы выключили <b>автоматические функции для него</b>, проверьте прокси и повторите попытку.
                        """,
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
                return await bot.send_message(
                    chat_id=account.user_id,
                    text=f"""
❌ Не удалось <b>подключиться к прокси</b> для хомяка {account.full_name}.

Мы выключили <b>автоматические функции для него</b>, проверьте прокси и повторите попытку.
                        """,
                )

            hamster.set_proxy(proxy_connector=proxy_connector)

            success_upgrades, account = await buy_profit_upgrades(
                uow=uow,
                account=account,
                upgrades=account.upgrades,
                hamster=hamster,
                sections=["Markets", "PR&Team", "Legal", "Specials"],
            )
            success_upgrades: Optional[list[HamsterUpgrade]]
            account: DBAccount

            trigger: IntervalTrigger = IntervalTrigger(
                seconds=calculate_autoupgrade_interval()
            )

            schedule: Schedule = await add_schedule(
                sched=sched,
                trigger=trigger,
                schedule_id=generate_schedule_id(
                    task_id=TaskIds.AUTOUPGRADE,
                    account_id=account_id,
                    user_id=account.user_id,
                ),
                task_id=TaskIds.AUTOUPGRADE,
                account_id=account.id,
            )

        if success_upgrades:
            try:
                await sync_upgrades(
                    repo=repo,
                    uow=uow,
                    account=account,
                    hamster=hamster,
                )
            except RequestError as error:
                await bot.send_message(
                    chat_id=account.user_id,
                    text=f"❌ Ошибка <b>авто-апгрейда</b>, аккаунт: {account.full_name} (<code>{account.id}</code>).",
                )
                return service.error(error)

            if account.config.is_autoupgrade_notifications:
                await bot.send_message(
                    chat_id=account.user_id,
                    text=await CustomJinja(
                        """
🐹 <b>Хомячок</b> {{ account.full_name }} (<code>{{ account.id }}</code>)
└ <b>Баланс:</b> <code>{{ "{:,}".format(account.balance_coins | int) }}</code>

💸 <b>Доход монет</b>
├ <b>В минуту:</b> <code>{{ "{:,}".format((account.earn_passive_per_sec * 60) | int) }}</code>
├ <b>В час:</b> <code>{{ "{:,}".format(account.earn_passive_per_hour | int) }}</code>
└ <b>В день:</b> <code>{{ "{:,}".format((account.earn_passive_per_hour * 24) | int) }}</code>

⏫ <b>Купленные апгрейды</b>
{% for upgrade in upgrades %}
• <code>{{ upgrade.type }}</code> | <b>Стоимость:</b> <code>{{ "{:,}".format(upgrade.price | int) }}</code> | До окупа: <code>{{ upgrade.profit_per_time | round(2) }}</code> ч.
{% endfor %}

🎊 <b>Авто-апгрейд:</b>
{% if next_run_autoupgrade %}
└ <b>Следующий запуск:</b> <code>{{ next_run_autoupgrade }}</code>
{% else %}
└ ⚠️ Не удалось получить <b>дату и время следующего запуска</b>.
{% endif %}
                        """,
                        upgrades=success_upgrades,
                        next_run_autoupgrade=(
                            format_datetime(
                                schedule.next_fire_time,
                                "short",
                                tzinfo=get_timezone("Europe/Moscow"),
                                locale="ru_RU",
                            )
                            if schedule
                            else None
                        ),
                        account=account,
                    ).render(),
                )


async def handle_autofarm(
    account_id: int,
    bot: Bot,
    hamster: HamsterKombat,
    config: AppConfig,
    session: async_sessionmaker[AsyncSession],
    engine: AsyncEngine,
    **_,
) -> None:
    async with SQLSessionContext(session_pool=session) as (repo, uow):
        account: Optional[DBAccount] = await repo.accounts.get_one(
            DBAccount.upgrades, DBAccount.config, account_id=account_id
        )

        account_proxy: Optional[DBAccountProxy] = await repo.proxies.get_one(
            config_id=account.config.id
        )

        async with config.postgres.build_scheduler(engine=engine) as sched:
            if account_proxy is None:
                await disable_account_proxy(
                    sched=sched, uow=uow, account=account, proxy=account_proxy
                )
                return await bot.send_message(
                    chat_id=account.user_id,
                    text=f"""
❌ Не удалось <b>подключиться к прокси</b> для хомяка {account.full_name}.

Мы выключили <b>автоматические функции для него</b>, проверьте прокси и повторите попытку.
                        """,
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
                return await bot.send_message(
                    chat_id=account.user_id,
                    text=f"""
❌ Не удалось <b>подключиться к прокси</b> для хомяка {account.full_name}.

Мы выключили <b>автоматические функции для него</b>, проверьте прокси и повторите попытку.
                        """,
                )

            hamster.set_proxy(proxy_connector=proxy_connector)

            energy: int = account.available_taps // account.earn_per_tap
            random_uniform: int = random.uniform(1.6, 1.8)
            random_count: int = int(energy // random_uniform)
            earn_per_tap_before: int = account.earn_per_tap
            available_taps_before: int = account.available_taps

            try:
                hamster_data: HamsterData = await hamster.tap(
                    bearer_token=account.token,
                    available_taps=account.available_taps,
                    count=random_count,
                )

                account: DBAccount = await sync_account(
                    uow=uow,
                    account=account,
                    hamster_data=hamster_data,
                )
            except RequestError as error:
                await bot.send_message(
                    chat_id=account.user_id,
                    text=f"❌ Ошибка <b>авто-фарма</b>, аккаунт: {account.full_name} (<code>{account.id}</code>).",
                )
                return service.error(error)

            schedule: Schedule = await process_schedule(
                sched=sched,
                action=SchedulerActions.RESCHEDULE,
                schedule_id=generate_schedule_id(
                    task_id=TaskIds.AUTOFARM,
                    account_id=account_id,
                    user_id=account.user_id,
                ),
                task_id=TaskIds.AUTOFARM,
                trigger=IntervalTrigger(seconds=account.config.autofarm_interval),
                account_id=account.id,
            )

            if account.config.is_autofarm_notifications:
                await bot.send_message(
                    chat_id=account.user_id,
                    text=await CustomJinja(
                        """
🐹 <b>Хомячок</b> {{ account.full_name }} (<code>{{ account.id }}</code>)
├ <b>Баланс:</b> <code>{{ "{:,}".format(account.balance_coins | int) }}</code>
├ <b>Монет за один тап:</b> <code>{{ account.earn_per_tap }}</code>
└ <b>Монет за всё время:</b> <code>{{ "{:,}".format(account.total_coins | int) }}</code>

👆 <b>Тапы</b>
├ <b>Доступно:</b> <code>{{ "{:,}".format(account.available_taps | int) }}</code>
└ <b>Максимум:</b> <code>{{ "{:,}".format(account.max_taps | int) }}</code>

⛏ <b>Автофарм</b>
├ <b>Тапнуто:</b> <code>{{ random_count }}</code> * <code>{{ earn_per_tap_before }}</code> (<code>{{ random_count * earn_per_tap_before }}</code>)
{% if next_run_autofarm %}
└ <b>Следующий запуск:</b> <code>{{ next_run_autofarm }}</code>
{% else %}
└ ⚠️ Не удалось получить <b>дату и время следующего запуска</b>.
{% endif %}
                        """,
                        earn_per_tap_before=earn_per_tap_before,
                        available_taps_before=available_taps_before,
                        random_uniform=random_uniform,
                        random_count=random_count,
                        energy=energy,
                        next_run_autofarm=(
                            format_datetime(
                                schedule.next_fire_time,
                                "short",
                                tzinfo=get_timezone("Europe/Moscow"),
                                locale="ru_RU",
                            )
                            if schedule
                            else None
                        ),
                        account=account,
                    ).render(),
                )


async def handle_night_sleep(
    random_seconds_after_midnight: int,
    bot: Bot,
    config: AppConfig,
    session: async_sessionmaker[AsyncSession],
    engine: AsyncEngine,
    **_,
) -> None:
    async with SQLSessionContext(session_pool=session) as (repo, uow):
        users: list[DBUser] = await repo.users.get_all(DBUser.accounts)
        for user in users:
            async with config.postgres.build_scheduler(engine=engine) as sched:
                random_seconds: int = random_seconds_after_midnight + random.randint(
                    10800, 18000
                )
                for account in user.accounts:
                    account: DBAccount

                    await add_schedule(
                        sched=sched,
                        trigger=IntervalTrigger(
                            seconds=random_seconds + calculate_autofarm_interval()
                        ),
                        schedule_id=generate_schedule_id(
                            task_id=TaskIds.AUTOFARM,
                            account_id=account.id,
                            user_id=user.id,
                        ),
                        task_id=TaskIds.AUTOFARM,
                        account_id=account.id,
                    )

                    await add_schedule(
                        sched=sched,
                        trigger=IntervalTrigger(
                            seconds=random_seconds + calculate_autoupgrade_interval()
                        ),
                        schedule_id=generate_schedule_id(
                            task_id=TaskIds.AUTOUPGRADE,
                            account_id=account.id,
                            user_id=user.id,
                        ),
                        task_id=TaskIds.AUTOUPGRADE,
                        account_id=account.id,
                    )

                    await add_schedule(
                        sched=sched,
                        trigger=IntervalTrigger(
                            seconds=random_seconds + calculate_autosync_interval()
                        ),
                        schedule_id=generate_schedule_id(
                            task_id=TaskIds.AUTOSYNC,
                            account_id=account.id,
                            user_id=user.id,
                        ),
                        task_id=TaskIds.AUTOSYNC,
                        account_id=account.id,
                    )

                await bot.send_message(
                    chat_id=user.id,
                    text=await CustomJinja(
                        """
🌙 <b>Автоматические функции</b> всех ваших аккаунтов поставлены на сон до <b>{{ next_run_time }}</b>

Это <b>необходимая процедура</b> для имитации реального человека.
                        """,
                        next_run_time=format_datetime(
                            datetime.now() + timedelta(seconds=random_seconds),
                            "short",
                            tzinfo=get_timezone("Europe/Moscow"),
                            locale="ru_RU",
                        ),
                    ).render(),
                )


async def on_start_account_boosts_dialog(
    _: CallbackQuery, __: Button, manager: DialogManager
):
    repo: Repository = manager.middleware_data["repo"]
    uow: UoW = manager.middleware_data["uow"]
    config: AppConfig = manager.middleware_data["config"]
    sched: AsyncScheduler = manager.middleware_data["sched"]
    hamster: HamsterKombat = manager.middleware_data["hamster"]

    account_id: int = manager.start_data["account_id"]

    account: Optional[DBAccount] = await repo.accounts.get_one(
        DBAccount.config,
        account_id=account_id,
    )
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
        return await manager.event.answer(
            f"""
❌ Не удалось подключиться к прокси для хомяка {account.full_name}.

Мы выключили автоматические функции для него, проверьте прокси и повторите попытку.
            """,
            show_alert=True,
        )

    hamster.set_proxy(proxy_connector=proxy_connector)

    try:
        await sync_boosts(
            repo=repo,
            uow=uow,
            account=account,
            hamster=hamster,
        )
    except RequestError as error:
        service.error(error)
        return await manager.event.answer(common_texts.UNKNOWN_ERROR_REQUEST_TEXT)

    data: dict[str, Any] = {"account_id": account_id}
    return await manager.start(states.AccountBoostsDialog.SELECT_BOOST, data=data)


async def on_select_boost_by_id(
    _: CallbackQuery, __: Button, manager: DialogManager, boost_id: int
):
    repo: Repository = manager.middleware_data["repo"]
    boost: Optional[DBAccountBoost] = await repo.boosts.get_one(
        DBAccountBoost.account, boost_id=boost_id
    )
    if boost is None:
        return await manager.event.answer(common_texts.BOOST_NOT_FOUND_TEXT)

    manager.dialog_data["boost_id"] = boost_id
    manager.dialog_data["boost_type"] = boost.type
    return await manager.switch_to(states.AccountBoostsDialog.INFO)


async def on_button_buy_boost(_: CallbackQuery, __: Button, manager: DialogManager):
    repo: Repository = manager.middleware_data["repo"]
    uow: UoW = manager.middleware_data["uow"]
    config: AppConfig = manager.middleware_data["config"]
    sched: AsyncScheduler = manager.middleware_data["sched"]
    hamster: HamsterKombat = manager.middleware_data["hamster"]

    account_id: int = manager.start_data["account_id"]
    boost_type: str = manager.dialog_data["boost_type"]

    account: Optional[DBAccount] = await repo.accounts.get_one(
        DBAccount.config,
        account_id=account_id,
    )
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
        return await manager.event.answer(
            f"""
❌ Не удалось подключиться к прокси для хомяка {account.full_name}.

Мы выключили автоматические функции для него, проверьте прокси и повторите попытку.
            """,
            show_alert=True,
        )

    hamster.set_proxy(proxy_connector=proxy_connector)

    try:
        hamster_data: HamsterData = await hamster.buy_boost(
            bearer_token=account.token, boost_id=boost_type
        )
        service.info("Bought boost: %d | %s", account.id, account.full_name)
        await sync_account(
            uow=uow,
            account=account,
            hamster_data=hamster_data,
        )
        await sync_boosts(
            repo=repo,
            uow=uow,
            account=account,
            hamster=hamster,
        )
    except RequestError as error:
        service.error(error)
        return await manager.event.answer(common_texts.UNKNOWN_ERROR_REQUEST_TEXT)


async def on_start_account_upgrades_dialog(
    _: CallbackQuery, __: Button, manager: DialogManager
):
    repo: Repository = manager.middleware_data["repo"]
    uow: UoW = manager.middleware_data["uow"]
    config: AppConfig = manager.middleware_data["config"]
    sched: AsyncScheduler = manager.middleware_data["sched"]
    hamster: HamsterKombat = manager.middleware_data["hamster"]

    account_id: int = manager.start_data["account_id"]

    account: DBAccount = await repo.accounts.get_one(
        DBAccount.config,
        account_id=account_id,
    )
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
        return await manager.event.answer(
            f"""
❌ Не удалось подключиться к прокси для хомяка {account.full_name}.

Мы выключили автоматические функции для него, проверьте прокси и повторите попытку.
            """,
            show_alert=True,
        )

    hamster.set_proxy(proxy_connector=proxy_connector)

    try:
        await sync_upgrades(
            repo=repo,
            uow=uow,
            account=account,
            hamster=hamster,
        )
    except RequestError as error:
        service.error(error)
        return await manager.event.answer(common_texts.UNKNOWN_ERROR_REQUEST_TEXT)

    data: dict[str, Any] = {"account_id": account_id, "section": "Markets"}
    return await manager.start(states.AccountUpgradesDialog.SELECT_UPGRADE, data=data)


async def on_start_upgrade_condition_dialog(
    _: CallbackQuery, __: Button, manager: DialogManager
):
    repo: Repository = manager.middleware_data["repo"]
    upgrade_id: int = manager.dialog_data["condition_upgrade_id"]

    upgrade: Optional[DBAccountUpgrade] = await repo.upgrades.get_one(
        DBAccountUpgrade.account, upgrade_id=upgrade_id
    )
    if upgrade is None:
        return await manager.event.answer(common_texts.UPGRADE_NOT_FOUND_TEXT)

    data: dict[str, Any] = {
        "upgrade_id": upgrade.id,
        "upgrade_type": upgrade.type,
        "account_id": upgrade.account.id,
    }

    return await manager.start(states.AccountUpgradeDialog.INFO, data=data)


async def on_select_upgrade_section(
    _: CallbackQuery, __: ManagedRadio, manager: DialogManager, section: str
):
    manager.start_data["section"] = section


async def on_select_upgrade_by_id(
    _: CallbackQuery, __: Button, manager: DialogManager, upgrade_id: int
):
    repo: Repository = manager.middleware_data["repo"]
    upgrade: Optional[DBAccountUpgrade] = await repo.upgrades.get_one(
        DBAccountUpgrade.account, upgrade_id=upgrade_id
    )
    if upgrade is None:
        return await manager.event.answer(common_texts.UPGRADE_NOT_FOUND_TEXT)

    data: dict[str, Any] = {
        "upgrade_id": upgrade.id,
        "upgrade_type": upgrade.type,
        "account_id": upgrade.account.id,
    }
    return await manager.start(states.AccountUpgradeDialog.INFO, data=data)


async def on_button_buy_upgrade(_: CallbackQuery, __: Button, manager: DialogManager):
    repo: Repository = manager.middleware_data["repo"]
    uow: UoW = manager.middleware_data["uow"]
    config: AppConfig = manager.middleware_data["config"]
    sched: AsyncScheduler = manager.middleware_data["sched"]
    hamster: HamsterKombat = manager.middleware_data["hamster"]

    account_id: int = manager.start_data["account_id"]
    upgrade_type: str = manager.start_data["upgrade_type"]

    account: Optional[DBAccount] = await repo.accounts.get_one(
        DBAccount.config,
        account_id=account_id,
    )
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
        return await manager.event.answer(
            f"""
❌ Не удалось подключиться к прокси для хомяка {account.full_name}.

Мы выключили автоматические функции для него, проверьте прокси и повторите попытку.
            """,
            show_alert=True,
        )

    hamster.set_proxy(proxy_connector=proxy_connector)

    try:
        hamster_data: Optional[HamsterData] = await hamster.buy_upgrade(
            bearer_token=account.token, upgrade_id=upgrade_type
        )
        service.info("Bought upgrade: %d | %s", account.id, account.full_name)
        await sync_account(
            uow=uow,
            account=account,
            hamster_data=hamster_data,
        )
        await sync_upgrades(
            repo=repo,
            uow=uow,
            account=account,
            hamster=hamster,
        )
    except RequestError as error:
        service.error(error)
        return await manager.event.answer(common_texts.UNKNOWN_ERROR_REQUEST_TEXT)


async def on_button_buy_profit_upgrades(
    _: CallbackQuery, __: Button, manager: DialogManager
):
    repo: Repository = manager.middleware_data["repo"]
    uow: UoW = manager.middleware_data["uow"]
    sched: AsyncScheduler = manager.middleware_data["sched"]
    config: AppConfig = manager.middleware_data["config"]
    hamster: HamsterKombat = manager.middleware_data["hamster"]

    account_id: int = manager.start_data["account_id"]
    account: Optional[DBAccount] = await repo.accounts.get_one(
        DBAccount.upgrades,
        DBAccount.config,
        account_id=account_id,
    )

    _: asyncio.Task = asyncio.create_task(
        on_button_buy_profit_upgrades_thread(
            repo=repo,
            uow=uow,
            sched=sched,
            account=account,
            hamster=hamster,
            config=config,
        )
    )
    return await manager.event.answer("Ожидайте...")


async def on_button_buy_profit_upgrades_thread(
    repo: Repository,
    uow: UoW,
    sched: AsyncScheduler,
    account: DBAccount,
    hamster: HamsterKombat,
    config: AppConfig,
):
    async with Bot(
        config.common.bot_token.get_secret_value(),
        default=DefaultBotProperties(parse_mode="HTML"),
    ) as bot:
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
            return await bot.send_message(
                chat_id=account.user_id,
                text=f"""
❌ Не удалось <b>подключиться к прокси</b> для хомяка {account.full_name}.

Мы выключили <b>автоматические функции для него</b>, проверьте прокси и повторите попытку.
                    """,
            )

        hamster.set_proxy(proxy_connector=proxy_connector)

        success_upgrades, account = await buy_profit_upgrades(
            uow=uow,
            account=account,
            upgrades=account.upgrades,
            hamster=hamster,
            sections=["Markets", "PR&Team", "Legal", "Specials"],
        )
        success_upgrades: Optional[list[HamsterUpgrade]]
        account: DBAccount

        try:
            await sync_upgrades(
                repo=repo,
                uow=uow,
                account=account,
                hamster=hamster,
            )
        except RequestError as error:
            return service.error(error)

        schedule: Optional[Schedule] = None
        if account.config.is_autoupgrade:
            schedule: Schedule = await add_schedule(
                sched=sched,
                trigger=IntervalTrigger(seconds=calculate_autoupgrade_interval()),
                schedule_id=generate_schedule_id(
                    task_id=TaskIds.AUTOUPGRADE,
                    account_id=account.id,
                    user_id=account.user_id,
                ),
                task_id=TaskIds.AUTOUPGRADE,
                account_id=account.id,
            )

        if success_upgrades:
            await bot.send_message(
                chat_id=account.user_id,
                text=await CustomJinja(
                    """
👍 <b>Профитные апгрейды</b> были <b>успешно</b> куплены вручную!

🐹 <b>Хомячок</b> {{ account.full_name }} (<code>{{ account.id }}</code>)
└ <b>Баланс:</b> <code>{{ "{:,}".format(account.balance_coins | int) }}</code>

⏫ <b>Купленные апгрейды</b>
{% for upgrade in upgrades %}
• <code>{{ upgrade.type }}</code> | <b>Стоимость:</b> <code>{{ "{:,}".format(upgrade.price | int) }}</code> | До окупа: <code>{{ upgrade.profit_per_time | round(2) }}</code> ч.
{% endfor %}

🎊 <b>Авто-апгрейд:</b>
{% if next_run_autoupgrade %}
└ <b>Следующий запуск:</b> <code>{{ next_run_autoupgrade }}</code>
{% else %}
└ ⚠️ Не удалось получить <b>дату и время следующего запуска</b>.
{% endif %}
                    """,
                    upgrades=success_upgrades,
                    next_run_autoupgrade=(
                        format_datetime(
                            schedule.next_fire_time,
                            "short",
                            tzinfo=get_timezone("Europe/Moscow"),
                            locale="ru_RU",
                        )
                        if schedule
                        else None
                    ),
                    account=account,
                ).render(),
            )
        else:
            await bot.send_message(
                chat_id=account.user_id, text="😕 Профитных апгрейдов не нашлось!"
            )
