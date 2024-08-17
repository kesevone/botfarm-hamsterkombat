from typing import Optional

from aiogram_dialog import DialogManager
from aiohttp_socks import ProxyConnector

from src.app_config import AppConfig
from src.database import Repository, UoW
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
from src.hamster import HamsterKombat


async def get_accounts_by_user_id(dialog_manager: DialogManager, **_):
    repo: Repository = dialog_manager.middleware_data["repo"]
    user: DBUser = dialog_manager.middleware_data["user"]
    user_id: str = dialog_manager.event.from_user.id
    accounts: list[Optional[DBAccount]] = await repo.accounts.get_all(
        DBAccount.total_coins.desc(), user_id=user_id
    )

    return {
        "accounts": accounts,
        "user": user,
        "is_accounts_limit": len(accounts) >= user.max_accounts,
    }


async def get_account_data(dialog_manager: DialogManager, **_):
    repo: Repository = dialog_manager.middleware_data["repo"]
    uow: UoW = dialog_manager.middleware_data["uow"]
    config: AppConfig = dialog_manager.middleware_data["config"]
    hamster: HamsterKombat = dialog_manager.middleware_data["hamster"]
    account_id: int = dialog_manager.start_data["account_id"]
    account: Optional[DBAccount] = await repo.accounts.get_one(
        DBAccount.boosts, DBAccount.tasks, account_id=account_id
    )
    account_cipher: Optional[DBAccountCipher] = await repo.ciphers.get_one(
        account_id=account.id
    )
    account_config: Optional[DBAccountConfig] = await repo.configs.get_one(
        account_id=account.id
    )
    account_upgrades: Optional[list[DBAccountUpgrade]] = await repo.upgrades.get_all(
        account_id=account.id, is_active=True, is_expired=False
    )
    account_daily_task: Optional[DBAccountTask] = await repo.tasks.get_one(
        task_type="streak_days", account_id=account.id
    )

    account_proxy: Optional[DBAccountProxy] = await repo.proxies.get_one(
        config_id=account_config.id
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

    dialog_manager.start_data["task_id"] = account_daily_task.type

    return {
        "account": account,
        "config": account_config,
        "boosts": account.boosts,
        "upgrades": account_upgrades,
        "tasks": account.tasks,
        "daily_task": account_daily_task,
        "cipher": account_cipher,
        "is_daily_task_completed": (
            account_daily_task.is_completed if account_daily_task else True
        ),
        "is_cipher_claimed": account_cipher.is_claimed if account_cipher else True,
        "proxy": account_proxy,
        "is_proxy_active": account_proxy and account_proxy.is_active,
    }


async def get_account_boosts(dialog_manager: DialogManager, **_):
    repo: Repository = dialog_manager.middleware_data["repo"]
    account_id: int = dialog_manager.start_data["account_id"]
    boosts: Optional[list[DBAccountBoost]] = await repo.boosts.get_all(
        account_id=account_id,
        sort_column=DBAccountBoost.price,
    )

    return {"boosts": boosts}


async def get_boost_data(dialog_manager: DialogManager, **_):
    repo: Repository = dialog_manager.middleware_data["repo"]
    boost_id: int = dialog_manager.dialog_data["boost_id"]
    boost: Optional[DBAccountBoost] = await repo.boosts.get_one(
        DBAccountBoost.account, boost_id=boost_id
    )

    return {
        "boost": boost,
        "is_active": boost.account.balance_coins > boost.price
        and boost.cooldown_seconds == 0,
    }


async def get_account_upgrades(dialog_manager: DialogManager, **_):
    repo: Repository = dialog_manager.middleware_data["repo"]
    account_id: int = dialog_manager.start_data["account_id"]
    section: str = dialog_manager.start_data["section"]
    upgrades: Optional[list[DBAccountUpgrade]] = await repo.upgrades.get_all(
        DBAccountUpgrade.is_active.desc(),
        DBAccountUpgrade.level.desc(),
        account_id=account_id,
        section=section,
    )
    await dialog_manager.find("sections_selector").set_checked(section)

    return {"upgrades": upgrades}


async def get_upgrade_data(dialog_manager: DialogManager, **_):
    repo: Repository = dialog_manager.middleware_data["repo"]
    upgrade_id: int = dialog_manager.start_data["upgrade_id"]
    upgrade: Optional[DBAccountUpgrade] = await repo.upgrades.get_one(
        DBAccountUpgrade.account, upgrade_id=upgrade_id
    )

    condition: Optional[DBAccountUpgrade] = await repo.upgrades.get_one(
        upgrade_id=upgrade.condition_id
    )

    dialog_manager.dialog_data["condition_upgrade_id"] = (
        condition.id if condition else None
    )

    return {
        "upgrade": upgrade,
        "condition": condition,
        "is_active": upgrade.is_active
        and not upgrade.is_expired
        and upgrade.account.balance_coins > upgrade.price
        and upgrade.cooldown_seconds == 0,
    }
