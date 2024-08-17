from datetime import datetime, timedelta
from typing import Any, Iterable, Mapping, Optional

from apscheduler import (
    AsyncScheduler,
    ConflictPolicy,
    Schedule,
    ScheduleLookupError,
)
from apscheduler.triggers.interval import IntervalTrigger

from src.enums import SchedulerActions, TaskIds
from src.utils.loggers import log_autofarm, log_autosync, log_autoupgrade, service


def log_schedule_action(text: str, task_id: TaskIds) -> None:
    if task_id == TaskIds.AUTOFARM:
        log_autofarm.info(text)
    elif task_id == TaskIds.AUTOUPGRADE:
        log_autoupgrade.info(text)
    elif task_id == TaskIds.AUTOSYNC:
        log_autosync.info(text)
    else:
        service.info(text)


def generate_schedule_id(
    task_id: TaskIds, account_id: Optional[int] = None, user_id: Optional[int] = None
) -> str:
    if account_id is None or user_id is None:
        return f"{task_id}"
    return f"{task_id}:{account_id}:{user_id}"


def parse_schedule_id(schedule_id: str) -> tuple[int, int]:
    account_id, user_id = schedule_id.split(":")
    return int(account_id), int(user_id)


async def add_schedule(
    sched: AsyncScheduler,
    trigger: IntervalTrigger,
    schedule_id: str,
    task_id: TaskIds,
    set_start_time: Optional[bool] = True,
    *args: Optional[Iterable],
    **kwargs: Optional[Mapping[str, Any]],
) -> Schedule:
    if set_start_time:
        trigger.start_time = datetime.now() + timedelta(seconds=trigger.seconds)

    await sched.add_schedule(
        func_or_task_id=task_id,
        id=schedule_id,
        trigger=trigger,
        conflict_policy=ConflictPolicy.replace,
        args=args,
        kwargs=kwargs,
    )

    schedule: Schedule = await sched.get_schedule(id=schedule_id)

    return schedule


async def process_schedule(
    sched: AsyncScheduler,
    action: SchedulerActions,
    schedule_id: str,
    task_id: Optional[TaskIds] = None,
    trigger: Optional[IntervalTrigger] = None,
    *args: Optional[Iterable],
    **kwargs: Optional[Mapping[str, Any]],
) -> Optional[Schedule]:
    try:
        schedule: Schedule = await sched.get_schedule(id=schedule_id)
    except ScheduleLookupError:
        return

    if action == SchedulerActions.GET:
        return schedule

    if action == SchedulerActions.REMOVE:
        await sched.remove_schedule(schedule_id)
        log_schedule_action(text=f"Schedule {schedule_id} removed.", task_id=task_id)

    elif action == SchedulerActions.PAUSE:
        await sched.pause_schedule(schedule_id)
        log_schedule_action(text=f"Schedule {schedule_id} paused.", task_id=task_id)
    elif action == SchedulerActions.RESUME:
        await sched.unpause_schedule(schedule_id)
        log_schedule_action(text=f"Schedule {schedule_id} unpaused.", task_id=task_id)
    elif action == SchedulerActions.RESCHEDULE:
        if trigger is None:
            return log_schedule_action(
                text=f"Trigger for the action {action} was not passed", task_id=task_id
            )

        trigger.start_time = datetime.now() + timedelta(seconds=trigger.seconds)
        sch_id: str = await sched.add_schedule(
            func_or_task_id=task_id,
            id=schedule_id,
            trigger=trigger,
            conflict_policy=ConflictPolicy.replace,
            args=args,
            kwargs=kwargs,
        )

        schedule: Schedule = await sched.get_schedule(id=sch_id)
        log_schedule_action(
            text=f"Schedule {schedule_id} rescheduled, next fire time: {schedule.next_fire_time}.",
            task_id=task_id,
        )
    else:
        log_schedule_action(
            text=f"Unknown action {action} for schedule {schedule_id}.", task_id=task_id
        )

    return schedule
