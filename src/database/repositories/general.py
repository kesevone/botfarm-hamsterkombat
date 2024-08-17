from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from .accounts import AccountsRepository
from .airdrop_tasks import AirdropTasksRepository
from .base import BaseRepository
from .boosts import BoostsRepository
from .ciphers import CiphersRepository
from .configs import ConfigsRepository
from .proxies import ProxiesRepository
from .tasks import TasksRepository
from .upgrades import UpgradesRepository
from .users import UsersRepository


class Repository(BaseRepository):
    """
    The general repository.
    """

    users: UsersRepository
    accounts: AccountsRepository
    configs: ConfigsRepository
    proxies: ProxiesRepository
    boosts: BoostsRepository
    upgrades: UpgradesRepository
    tasks: TasksRepository
    ciphers: CiphersRepository
    airdrop_tasks: AirdropTasksRepository

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session=session)
        self.users = UsersRepository(session=session)
        self.accounts = AccountsRepository(session=session)
        self.configs = ConfigsRepository(session=session)
        self.proxies = ProxiesRepository(session=session)
        self.boosts = BoostsRepository(session=session)
        self.upgrades = UpgradesRepository(session=session)
        self.ciphers = CiphersRepository(session=session)
        self.tasks = TasksRepository(session=session)
        self.airdrop_tasks = AirdropTasksRepository(session=session)
