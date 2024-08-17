from enum import StrEnum


class ClickerEndpoints(StrEnum):
    SYNC = "/clicker/sync"
    TAP = "/clicker/tap"
    BOOSTS = "/clicker/boosts-for-buy"
    UPGRADES = "/clicker/upgrades-for-buy"
    TASKS = "/clicker/list-tasks"
    BUY_UPGRADE = "/clicker/buy-upgrade"
    BUY_BOOST = "/clicker/buy-boost"
    CHECK_TASK = "/clicker/check-task"
    CLAIM_DAILY_CIPHER = "/clicker/claim-daily-cipher"
    CLAIM_DAILY_COMBO = "/clicker/claim-daily-combo"
    CONFIG = "/clicker/config"


class AuthEndpoints(StrEnum):
    WEBAPP = "/auth/auth-by-telegram-webapp"
    TELEGRAM = "/auth/me-telegram"
    IP = "/ip"
