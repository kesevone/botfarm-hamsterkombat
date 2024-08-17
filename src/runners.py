from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING

from aiogram import Bot, Dispatcher, loggers
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncEngine, AsyncSession

from src.hamster import HamsterKombat
from .enums import TaskIds
from .telegram.dialogs import user
from .telegram.dialogs.user.accounts.handlers import (
    handle_autofarm,
    handle_autosync,
    handle_autoupgrade,
)

if TYPE_CHECKING:
    from .app_config import AppConfig


async def polling_startup(bot: Bot, config: AppConfig) -> None:
    if config.common.drop_pending_updates:
        await bot.delete_webhook(drop_pending_updates=True)
        loggers.dispatcher.info("Updates skipped successfully")


async def run_polling(dp: Dispatcher, bot: Bot) -> None:
    dp.startup.register(polling_startup)
    dp.include_routers(user.router)

    session: async_sessionmaker[AsyncSession] = dp["db_session"]
    engine: AsyncEngine = dp["engine"]
    hamster: HamsterKombat = dp["hamster"]
    config: AppConfig = dp["config"]

    async with config.postgres.build_scheduler(engine=engine) as sched:
        await sched.configure_task(
            TaskIds.AUTOFARM,
            func=partial(
                handle_autofarm,
                config=config,
                bot=bot,
                hamster=hamster,
                session=session,
                engine=engine,
            ),
            misfire_grace_time=10,
        )

        await sched.configure_task(
            TaskIds.AUTOUPGRADE,
            func=partial(
                handle_autoupgrade,
                config=config,
                bot=bot,
                hamster=hamster,
                session=session,
                engine=engine,
            ),
            misfire_grace_time=10,
        )

        await sched.configure_task(
            TaskIds.AUTOSYNC,
            func=partial(
                handle_autosync,
                config=config,
                bot=bot,
                hamster=hamster,
                session=session,
                engine=engine,
            ),
            misfire_grace_time=10,
        )

        # await sched.configure_task(
        #     TaskIds.NIGHT_SLEEP,
        #     func=partial(
        #         handle_night_sleep,
        #         config=config,
        #         bot=bot,
        #         hamster=hamster,
        #         session=session,
        #         engine=engine,
        #     ),
        #     misfire_grace_time=10,
        # )
        #
        # now = datetime.now()
        # midnight = datetime.combine(now + timedelta(days=1), time())
        # seconds_until_midnight = (midnight - now).seconds
        # random_seconds = seconds_until_midnight + random.randint(1800, 3600)
        #
        # await add_schedule(
        #     sched=sched,
        #     trigger=IntervalTrigger(
        #         seconds=random_seconds,
        #     ),
        #     schedule_id="night_sleep",
        #     task_id=TaskIds.NIGHT_SLEEP,
        #     random_seconds_after_midnight=random_seconds
        # )

        dp["sched"] = sched
        await sched.start_in_background()
        return await dp.start_polling(bot)
