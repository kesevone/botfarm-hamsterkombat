from enum import StrEnum


class SchedulerActions(StrEnum):
    GET = "get"
    REMOVE = "delete"
    PAUSE = "pause"
    RESUME = "resume"
    RESCHEDULE = "reschedule"
