from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import false, ForeignKey, func, true
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.enums.protocols import ProxyProtocol
from src.hamster.enums import TaskPeriodicity
from .base import (
    Base,
    Int64,
    IntPK,
    TimeStampMixin,
)


class DBUser(Base, TimeStampMixin):
    __tablename__ = "users"

    id: Mapped[IntPK]
    full_name: Mapped[str]
    username: Mapped[Optional[str]]
    max_accounts: Mapped[Optional[int]] = mapped_column(server_default="0")
    is_active: Mapped[bool] = mapped_column(server_default=true())

    accounts: Mapped[Optional[list[DBAccount]]] = relationship(
        back_populates="user",
        cascade="all, delete, delete-orphan",
        passive_deletes=True,
        lazy="noload",
    )

    @classmethod
    def create(
        cls,
        user_id: int,
        full_name: str,
        username: Optional[str] = None,
        max_accounts: Optional[int] = 0,
        is_active: Optional[bool] = True,
    ) -> DBUser:
        return cls(
            id=user_id,
            full_name=full_name,
            username=username,
            max_accounts=max_accounts,
            is_active=is_active,
        )

    def set_max_accounts(self, max_accounts: int) -> None:
        self.max_accounts = max_accounts

    def set_is_active(self, is_active: bool) -> None:
        self.is_active = is_active


class DBAccount(Base, TimeStampMixin):
    __tablename__ = "accounts"

    id: Mapped[IntPK]
    user_id: Mapped[Optional[Int64]] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE")
    )
    full_name: Mapped[str]
    username: Mapped[Optional[str]]
    token: Mapped[str]
    photos: Mapped[Optional[list]]
    referrals_count: Mapped[Optional[int]]
    level: Mapped[Optional[int]]
    total_coins: Mapped[Optional[float]]
    balance_coins: Mapped[Optional[float]]
    available_taps: Mapped[Optional[int]]
    max_taps: Mapped[Optional[int]]
    earn_per_tap: Mapped[Optional[int]]
    earn_passive_per_sec: Mapped[Optional[float]]
    earn_passive_per_hour: Mapped[Optional[float]]
    last_passive_earn: Mapped[Optional[float]]
    taps_recover_per_sec: Mapped[Optional[int]]

    user: Mapped[Optional[DBUser]] = relationship(
        back_populates="accounts", lazy="noload"
    )
    cipher: Mapped[DBAccountCipher] = relationship(
        back_populates="account",
        cascade="all, delete, delete-orphan",
        passive_deletes=True,
        lazy="noload",
    )
    config: Mapped[DBAccountConfig] = relationship(
        back_populates="account",
        cascade="all, delete, delete-orphan",
        passive_deletes=True,
        lazy="noload",
    )
    boosts: Mapped[list[DBAccountBoost]] = relationship(
        back_populates="account",
        cascade="all, delete, delete-orphan",
        passive_deletes=True,
        lazy="noload",
    )
    upgrades: Mapped[list[DBAccountUpgrade]] = relationship(
        back_populates="account",
        cascade="all, delete, delete-orphan",
        passive_deletes=True,
        lazy="noload",
    )
    tasks: Mapped[list[DBAccountTask]] = relationship(
        back_populates="account",
        cascade="all, delete, delete-orphan",
        passive_deletes=True,
        lazy="noload",
    )
    airdrop_tasks: Mapped[list[DBAccountAirdropTasks]] = relationship(
        back_populates="account",
        cascade="all, delete, delete-orphan",
        passive_deletes=True,
        lazy="noload",
    )

    @classmethod
    def create(
        cls,
        account_id: int,
        full_name: str,
        token: str,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        **kwargs: Any,
    ) -> DBAccount:
        return cls(
            id=account_id,
            user_id=user_id,
            full_name=full_name,
            token=token,
            username=username,
            **kwargs,
        )

    def set_data(self, **kwargs) -> None:
        try:
            for key, value in kwargs.items():
                self.__setattr__(key, value)
        except AttributeError:
            pass

    def set_full_name(self, full_name: str) -> None:
        self.full_name = full_name

    def set_username(self, username: str) -> None:
        self.username = username


class DBAccountCipher(Base, TimeStampMixin):
    __tablename__ = "account_ciphers"

    id: Mapped[IntPK]
    account_id: Mapped[Int64] = mapped_column(
        ForeignKey("accounts.id", ondelete="CASCADE")
    )
    bonus_coins: Mapped[Optional[int]] = mapped_column(server_default="0")
    cipher: Mapped[Optional[str]]
    is_claimed: Mapped[Optional[bool]] = mapped_column(server_default=false())
    remain_seconds: Mapped[Optional[int]] = mapped_column(server_default="0")

    account: Mapped[DBAccount] = relationship(
        back_populates="cipher",
        lazy="noload",
    )

    @classmethod
    def create(
        cls,
        account_id: int,
        bonus_coins: int,
        cipher: str,
        is_claimed: bool,
        remain_seconds: int,
        **kwargs: Any,
    ) -> DBAccountCipher:
        return cls(
            account_id=account_id,
            bonus_coins=bonus_coins,
            cipher=cipher,
            is_claimed=is_claimed,
            remain_seconds=remain_seconds,
            **kwargs,
        )

    def set_data(self, **kwargs) -> None:
        try:
            for key, value in kwargs.items():
                self.__setattr__(key, value)
        except AttributeError:
            pass


class DBAccountConfig(Base, TimeStampMixin):
    __tablename__ = "account_configs"

    id: Mapped[IntPK]
    account_id: Mapped[Int64] = mapped_column(
        ForeignKey("accounts.id", ondelete="CASCADE")
    )
    autofarm_interval: Mapped[Optional[int]] = mapped_column(server_default="1800")
    is_autofarm_notifications: Mapped[Optional[bool]] = mapped_column(
        server_default=true()
    )
    autoupgrade_interval: Mapped[Optional[int]] = mapped_column(server_default="300")
    autoupgrade_limit: Mapped[Optional[int]] = mapped_column(server_default="0")
    limit_percent: Mapped[Optional[int]] = mapped_column(server_default="0")
    is_autoupgrade_notifications: Mapped[Optional[bool]] = mapped_column(
        server_default=true()
    )
    autosync_interval: Mapped[Optional[int]] = mapped_column(server_default="3600")
    is_autosync_notifications: Mapped[Optional[bool]] = mapped_column(
        server_default=false()
    )
    is_autofarm: Mapped[Optional[bool]] = mapped_column(server_default=false())
    is_autoupgrade: Mapped[Optional[bool]] = mapped_column(server_default=false())
    is_autosync: Mapped[Optional[bool]] = mapped_column(server_default=true())
    is_active: Mapped[Optional[bool]] = mapped_column(server_default=true())

    account: Mapped[DBAccount] = relationship(back_populates="config", lazy="noload")
    proxies: Mapped[list[DBAccountProxy]] = relationship(
        back_populates="config",
        cascade="all, delete, delete-orphan",
        passive_deletes=True,
        lazy="noload",
    )

    @classmethod
    def create(
        cls,
        account_id: int,
        autofarm_interval: Optional[int] = 600,
        is_autofarm_notifications: Optional[bool] = None,
        autoupgrade_interval: Optional[int] = 600,
        autoupgrade_limit: Optional[int] = 0,
        limit_percent: Optional[int] = 50,
        is_autoupgrade_notifications: Optional[bool] = None,
        autosync_interval: Optional[int] = 3600,
        is_autosync_notifications: Optional[bool] = None,
        is_autofarm: Optional[bool] = None,
        is_autoupgrade: Optional[bool] = None,
        is_active: Optional[bool] = None,
    ) -> DBAccountConfig:
        return cls(
            account_id=account_id,
            autofarm_interval=autofarm_interval,
            is_autofarm_notifications=is_autofarm_notifications,
            autoupgrade_interval=autoupgrade_interval,
            autoupgrade_limit=autoupgrade_limit,
            limit_percent=limit_percent,
            is_autoupgrade_notifications=is_autoupgrade_notifications,
            autosync_interval=autosync_interval,
            is_autosync_notifications=is_autosync_notifications,
            is_autofarm=is_autofarm,
            is_autoupgrade=is_autoupgrade,
            is_active=is_active,
        )

    def set_data(self, **kwargs) -> None:
        try:
            for key, value in kwargs.items():
                self.__setattr__(key, value)
        except AttributeError:
            pass

    def set_autofarm_interval(self, autofarm_interval: int) -> None:
        self.autofarm_interval = autofarm_interval

    def set_autofarm_notifications(self, is_autofarm_notifications: bool) -> None:
        self.is_autofarm_notifications = is_autofarm_notifications

    def set_autoupgrade_interval(self, autoupgrade_interval: int) -> None:
        self.autoupgrade_interval = autoupgrade_interval

    def set_autoupgrade_limit(self, autoupgrade_limit: int) -> None:
        self.autoupgrade_limit = autoupgrade_limit

    def set_limit_percent(self, limit_percent: int) -> None:
        self.limit_percent = limit_percent

    def set_autoupgrade_notifications(self, is_autoupgrade_notifications: bool) -> None:
        self.is_autoupgrade_notifications = is_autoupgrade_notifications

    def set_autosync_interval(self, autosync_interval: int) -> None:
        self.autosync_interval = autosync_interval

    def set_autosync_notifications(self, is_autosync_notifications: bool) -> None:
        self.is_autosync_notifications = is_autosync_notifications

    def set_is_autofarm(self, is_autofarm: bool) -> None:
        self.is_autofarm = is_autofarm

    def set_is_autoupgrade(self, is_autoupgrade: bool) -> None:
        self.is_autoupgrade = is_autoupgrade

    def set_is_autosync(self, is_autosync: bool) -> None:
        self.is_autosync = is_autosync

    def set_is_active(self, is_active: bool) -> None:
        self.is_active = is_active


class DBAccountProxy(Base, TimeStampMixin):
    __tablename__ = "account_proxies"

    id: Mapped[IntPK]
    config_id: Mapped[Int64] = mapped_column(
        ForeignKey("account_configs.id", ondelete="CASCADE")
    )
    protocol: Mapped[ProxyProtocol]
    host: Mapped[str]
    port: Mapped[int]
    username: Mapped[str]
    password: Mapped[str]
    timeout: Mapped[Optional[int]] = mapped_column(server_default="0")
    is_active: Mapped[bool] = mapped_column(server_default=true())

    config: Mapped[DBAccountConfig] = relationship(
        back_populates="proxies", lazy="noload"
    )

    @classmethod
    def create(
        cls,
        config_id: int,
        protocol: ProxyProtocol,
        host: str,
        port: int,
        username: str,
        password: str,
        timeout: Optional[int] = 10,
        is_active: bool = True,
    ) -> DBAccountProxy:
        return cls(
            config_id=config_id,
            protocol=protocol,
            host=host,
            port=port,
            username=username,
            password=password,
            timeout=timeout,
            is_active=is_active,
        )

    @property
    def url(self):
        return (
            f"{self.protocol}://{self.username}:{self.password}@{self.host}:{self.port}"
        )

    def set_data(self, **kwargs) -> None:
        try:
            for key, value in kwargs.items():
                self.__setattr__(key, value)
        except AttributeError:
            pass


class DBAccountBoost(Base, TimeStampMixin):
    __tablename__ = "account_boosts"

    id: Mapped[IntPK]
    type: Mapped[str]
    name: Mapped[Optional[str]]
    desc: Mapped[Optional[str]]
    account_id: Mapped[Int64] = mapped_column(
        ForeignKey("accounts.id", ondelete="CASCADE")
    )
    level: Mapped[int]
    price: Mapped[float]
    cooldown_seconds: Mapped[int]
    earn_per_tap: Mapped[int]
    earn_per_tap_delta: Mapped[int]
    max_taps: Mapped[int]
    max_taps_delta: Mapped[int]
    last_upgrade_at: Mapped[Optional[datetime]] = mapped_column(
        server_default=func.now()
    )

    account: Mapped[DBAccount] = relationship(back_populates="boosts", lazy="noload")

    @classmethod
    def create(
        cls,
        boost_type: str,
        account_id: int,
        level: int,
        price: float,
        cooldown_seconds: int,
        earn_per_tap: int,
        earn_per_tap_delta: int,
        max_taps: int,
        max_taps_delta: int,
        name: Optional[str] = None,
        desc: Optional[str] = None,
        last_upgrade_at: Optional[datetime] = None,
    ) -> DBAccountBoost:
        return cls(
            type=boost_type,
            name=name,
            desc=desc,
            account_id=account_id,
            level=level,
            price=price,
            cooldown_seconds=cooldown_seconds,
            earn_per_tap=earn_per_tap,
            earn_per_tap_delta=earn_per_tap_delta,
            max_taps=max_taps,
            max_taps_delta=max_taps_delta,
            last_upgrade_at=last_upgrade_at,
        )

    def set_data(self, **kwargs) -> None:
        try:
            for key, value in kwargs.items():
                self.__setattr__(key, value)
        except AttributeError:
            pass


class DBAccountUpgrade(Base, TimeStampMixin):
    __tablename__ = "account_upgrades"

    id: Mapped[IntPK]
    type: Mapped[str]
    name: Mapped[str]
    section: Mapped[str]
    condition_id: Mapped[Optional[Int64]] = mapped_column(
        ForeignKey("account_upgrades.id", ondelete="CASCADE")
    )
    account_id: Mapped[Int64] = mapped_column(
        ForeignKey("accounts.id", ondelete="CASCADE")
    )
    level: Mapped[int]
    price: Mapped[float]
    profit_per_hour: Mapped[float]
    cooldown_seconds: Mapped[Optional[int]] = mapped_column(server_default="0")
    is_expired: Mapped[Optional[bool]] = mapped_column(server_default=false())
    is_active: Mapped[Optional[bool]] = mapped_column(server_default=true())
    last_upgrade_at: Mapped[Optional[datetime]] = mapped_column(
        server_default=func.now()
    )

    account: Mapped[DBAccount] = relationship(back_populates="upgrades", lazy="noload")
    condition: Mapped[DBAccountUpgrade] = relationship(
        remote_side=[condition_id], join_depth=2
    )

    @classmethod
    def create(
        cls,
        upgrade_type: str,
        name: str,
        section: str,
        account_id: int,
        level: int,
        price: float,
        profit_per_hour: float,
        condition_id: Optional[int] = None,
        cooldown_seconds: Optional[int] = 0,
        is_expired: Optional[bool] = False,
        is_active: Optional[bool] = True,
        last_upgrade_at: Optional[datetime] = None,
    ) -> DBAccountUpgrade:
        return cls(
            type=upgrade_type,
            name=name,
            condition_id=condition_id,
            section=section,
            account_id=account_id,
            level=level,
            price=price,
            profit_per_hour=profit_per_hour,
            cooldown_seconds=cooldown_seconds,
            is_expired=is_expired,
            is_active=is_active,
            last_upgrade_at=last_upgrade_at,
        )

    def set_data(self, **kwargs) -> None:
        try:
            for key, value in kwargs.items():
                self.__setattr__(key, value)
        except AttributeError:
            pass


class DBAccountTask(Base, TimeStampMixin):
    __tablename__ = "account_tasks"

    id: Mapped[IntPK]
    type: Mapped[str]
    account_id: Mapped[Int64] = mapped_column(
        ForeignKey("accounts.id", ondelete="CASCADE")
    )
    reward_coins: Mapped[Optional[int]]
    days: Mapped[Optional[int]]
    periodicity: Mapped[Optional[TaskPeriodicity]]
    is_completed: Mapped[Optional[bool]] = mapped_column(server_default=false())
    completed_at: Mapped[Optional[datetime]] = mapped_column(server_default=func.now())

    account: Mapped[DBAccount] = relationship(back_populates="tasks", lazy="noload")

    @classmethod
    def create(
        cls,
        task_type: str,
        account_id: int,
        days: Optional[int] = None,
        reward_coins: Optional[int] = None,
        periodicity: Optional[TaskPeriodicity] = None,
        is_completed: Optional[bool] = False,
        completed_at: Optional[datetime] = None,
    ) -> DBAccountTask:
        return cls(
            type=task_type,
            account_id=account_id,
            days=days,
            reward_coins=reward_coins,
            periodicity=periodicity,
            is_completed=is_completed,
            completed_at=completed_at,
        )

    def set_data(self, **kwargs) -> None:
        try:
            for key, value in kwargs.items():
                self.__setattr__(key, value)
        except AttributeError:
            pass


class DBAccountAirdropTasks(Base, TimeStampMixin):
    __tablename__ = "airdrop_tasks"

    id: Mapped[IntPK]
    type: Mapped[str]
    account_id: Mapped[Int64] = mapped_column(
        ForeignKey("accounts.id", ondelete="CASCADE")
    )

    account: Mapped[DBAccount] = relationship(
        back_populates="airdrop_tasks", lazy="noload"
    )

    @classmethod
    def create(
        cls,
        airdrop_task_type: str,
        account_id: int,
        completed_at: Optional[datetime] = None,
    ) -> DBAccountAirdropTasks:
        return cls(
            type=airdrop_task_type, account_id=account_id, completed_at=completed_at
        )
