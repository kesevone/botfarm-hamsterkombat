from .auth_data import AuthData
from .hamster_data import (
    HamsterBoost,
    HamsterBoosts,
    HamsterConfig,
    HamsterDailyCipher,
    HamsterDailyCombo,
    HamsterData,
    HamsterIPData,
    HamsterTask,
    HamsterTasks,
    HamsterUpgrade,
    HamsterUpgrades,
)
from .user_data import UserData

__all__ = [
    "AuthData",
    "UserData",
    "HamsterData",
    "HamsterBoosts",
    "HamsterBoost",
    "HamsterUpgrades",
    "HamsterUpgrade",
    "HamsterTask",
    "HamsterTasks",
    "HamsterDailyCipher",
    "HamsterConfig",
    "HamsterIPData",
    "HamsterDailyCombo",
]
