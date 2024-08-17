from __future__ import annotations

import base64
import re
from datetime import datetime
from typing import Optional, Self

from pydantic import BaseModel, Field, model_validator


class HamsterData(BaseModel):
    id: str
    total_coins: Optional[float] = Field(0.0, alias="totalCoins")
    balance_coins: Optional[float] = Field(0.0, alias="balanceCoins")
    level: Optional[int] = Field(0, alias="level")
    available_taps: Optional[int] = Field(0, alias="availableTaps")
    last_sync_update: Optional[int] = Field(0, alias="lastSyncUpdate")
    referrals_count: Optional[int] = Field(0, alias="referralsCount")
    max_taps: Optional[int] = Field(0, alias="maxTaps")
    earn_per_tap: Optional[int] = Field(0, alias="earnPerTap")
    earn_passive_per_sec: Optional[float] = Field(0.0, alias="earnPassivePerSec")
    earn_passive_per_hour: Optional[float] = Field(0.0, alias="earnPassivePerHour")
    last_passive_earn: Optional[float] = Field(0.0, alias="lastPassiveEarn")
    taps_recover_per_sec: Optional[float] = Field(0.0, alias="tapsRecoverPerSec")

    boosts: Optional[dict[str, HamsterBoost]] = None
    upgrades: Optional[dict[str, HamsterUpgrade]] = None
    tasks: Optional[dict[str, HamsterTask]] = None

    @model_validator(mode="after")
    def timestamp2datetime(self) -> Self:
        if self.last_sync_update is not None:
            self.last_sync_update = datetime.fromtimestamp(self.last_sync_update)

        return self


class HamsterConfig(BaseModel):
    clicker_config: Optional[ClickerConfig] = Field(None, alias="clickerConfig")
    daily_cipher: Optional[HamsterDailyCipher] = Field(None, alias="dailyCipher")


class ClickerConfig(BaseModel):
    airdrop_tasks: Optional[list[dict]] = Field(None, alias="airdropTasks")
    boosts: Optional[list[dict]] = None
    exchanges: Optional[list[dict]] = None
    guid_link: Optional[dict] = Field(None, alias="guidLink")
    level_up: Optional[dict] = Field(None, alias="levelUp")
    max_passive_dt_seconds: Optional[int] = Field(None, alias="maxPassiveDtSeconds")
    tasks: Optional[list[dict]] = None
    upgrades: Optional[list[dict]] = None
    user_levels_balance_coins: Optional[list[dict]] = Field(
        None, alias="userLevels_balanceCoins"
    )


class HamsterDailyCipher(BaseModel):
    bonus_coins: Optional[int] = Field(0, alias="bonusCoins")
    cipher: Optional[str] = None
    is_claimed: Optional[bool] = Field(None, alias="isClaimed")
    remain_seconds: Optional[int] = Field(None, alias="remainSeconds")

    @model_validator(mode="after")
    def decode_cipher(self) -> Self:
        if self.cipher is not None:
            t = re.sub(r"^(.{3})\d+(.*)", r"\1\2", self.cipher)
            self.cipher = base64.b64decode(t).decode("utf-8")

        return self


class HamsterBoosts(BaseModel):
    boosts: Optional[list[HamsterBoost]] = None


class HamsterBoost(BaseModel):
    type: str = Field(..., alias="id")
    level: Optional[int] = Field(0, alias="level")
    price: Optional[float] = Field(0.0, alias="price")
    cooldown_seconds: Optional[int] = Field(0, alias="cooldownSeconds")
    earn_per_tap: Optional[int] = Field(0, alias="earnPerTap")
    earn_per_tap_delta: Optional[int] = Field(0, alias="earnPerTapDelta")
    max_taps: Optional[int] = Field(0, alias="maxTaps")
    max_taps_delta: Optional[int] = Field(0, alias="maxTapsDelta")
    last_upgrade_at: Optional[float] = Field(None, alias="lastUpgradeAt")

    @model_validator(mode="after")
    def timestamp2datetime(self) -> Self:
        if self.last_upgrade_at is not None:
            self.last_upgrade_at = datetime.fromtimestamp(self.last_upgrade_at)

        return self


class HamsterUpgrades(BaseModel):
    upgrades: Optional[list[HamsterUpgrade]] = Field(None, alias="upgradesForBuy")
    daily_combo: Optional[HamsterDailyCombo] = Field(None, alias="dailyCombo")


class HamsterUpgrade(BaseModel):
    type: str = Field(..., alias="id")
    name: Optional[str] = None
    condition: Optional[HamsterCondition] = None
    section: Optional[str] = None
    level: Optional[int] = 0
    price: Optional[float] = 0.0
    profit_per_time: Optional[float] = Field(0.0, alias="profitPerTime")
    profit_per_hour: Optional[float] = Field(0.0, alias="profitPerHour")
    cooldown_seconds: Optional[int] = Field(0, alias="cooldownSeconds")
    is_expired: Optional[bool] = Field(None, alias="isExpired")
    is_active: Optional[bool] = Field(None, alias="isAvailable")
    snapshot_referrals_count: Optional[int] = Field(
        None, alias="snapshotReferralsCount"
    )
    last_upgrade_at: Optional[float | datetime] = Field(None, alias="lastUpgradeAt")

    @model_validator(mode="after")
    def timestamp2datetime(self) -> Self:
        if self.last_upgrade_at is not None and isinstance(self.last_upgrade_at, float):
            self.last_upgrade_at = datetime.fromtimestamp(self.last_upgrade_at)

        return self


class HamsterDailyCombo(BaseModel):
    upgrade_ids: Optional[list] = Field([], alias="upgradeIds")
    bonus_coins: Optional[int] = Field(0, alias="bonusCoins")
    is_claimed: Optional[bool] = Field(None, alias="isClaimed")
    remain_seconds: Optional[int] = Field(None, alias="remainSeconds")
    actual_date: Optional[str] = Field(None, alias="date")


class HamsterCondition(BaseModel):
    level: Optional[int] = 0
    upgrade_type: Optional[str] = Field(None, alias="upgradeId")
    link: Optional[str] = None
    links: Optional[list] = None
    type: Optional[str] = Field(None, alias="_type")


class HamsterTasks(BaseModel):
    tasks: Optional[list[HamsterTask]] = None


class HamsterTask(BaseModel):
    type: str = Field(..., alias="id")
    days: Optional[int] = None
    reward_coins: Optional[int] = Field(0, alias="rewardCoins")
    periodicity: Optional[str] = None
    is_completed: Optional[bool] = Field(None, alias="isCompleted")
    completed_at: Optional[str] = Field(None, alias="completed_at")

    @model_validator(mode="after")
    def str2datetime(self) -> Self:
        if self.completed_at is not None and isinstance(self.completed_at, str):
            self.completed_at = datetime.strptime(
                self.completed_at, "%Y-%m-%dT%H:%M:%S.%fZ"
            )

        return self


class HamsterIPData(BaseModel):
    ip: Optional[str] = None
    country_code: Optional[str] = None
    city_name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    asn: Optional[str] = None
    asn_org: Optional[str] = None
