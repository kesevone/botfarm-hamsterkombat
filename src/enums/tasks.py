from enum import StrEnum


class TaskIds(StrEnum):
    AUTOFARM = "handle_autofarm"
    AUTOUPGRADE = "handle_autoupgrade"
    TICK = "handle_tick"
    NIGHT_SLEEP = "handle_night_sleep"
    AUTOSYNC = "handle_autosync"
    CIPHER = "handle_cipher"
    SET_CIPHER = "set_cipher"
