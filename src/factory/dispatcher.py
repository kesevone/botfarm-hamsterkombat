from __future__ import annotations

from aiogram import Dispatcher
from aiogram.fsm.storage.memory import SimpleEventIsolation
from aiogram.fsm.storage.redis import DefaultKeyBuilder, RedisStorage
from aiogram.utils.callback_answer import CallbackAnswerMiddleware
from aiogram_dialog import setup_dialogs
from aiogram_dialog.api.entities import DIALOG_EVENT_NAME
from apscheduler.datastores.sqlalchemy import SQLAlchemyDataStore
from apscheduler.eventbrokers.asyncpg import AsyncpgEventBroker
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncEngine, AsyncSession

from src.app_config import AppConfig
from src.database import Base, create_pool
from src.hamster import HamsterKombat
from src.telegram.middlewares import (
    DBSessionMiddleware,
    UserMiddleware,
)
from src.utils import msgspec_json as mjson


def _setup_outer_middlewares(dp: Dispatcher, config: AppConfig) -> None:
    engine, session = create_pool(
        dsn=config.postgres.build_dsn(), enable_logging=config.common.sqlalchemy_logging
    )
    session: async_sessionmaker[AsyncSession]
    engine: AsyncEngine
    dp["engine"] = engine
    dp["db_session"] = session

    for middleware in [
        DBSessionMiddleware(session=session),
        UserMiddleware(),
        # SchedulerMiddleware(),
    ]:
        dp.update.outer_middleware(middleware)
        dp.observers[DIALOG_EVENT_NAME].outer_middleware(middleware)


def _setup_inner_middlewares(dp: Dispatcher) -> None:
    dp.callback_query.middleware(CallbackAnswerMiddleware())


async def create_dispatcher(config: AppConfig) -> Dispatcher:
    redis: Redis = config.redis.build_client()

    hamster: HamsterKombat = HamsterKombat(base_url=config.hamster.base_url)

    dp: Dispatcher = Dispatcher(
        name="main_dispatcher",
        storage=RedisStorage(
            redis=redis,
            json_loads=mjson.decode,
            json_dumps=mjson.encode,
            key_builder=DefaultKeyBuilder(with_destiny=True),
        ),
        hamster=hamster,
        redis=redis,
        config=config,
        events_isolation=SimpleEventIsolation(),
    )
    bg_manager_factory = setup_dialogs(router=dp)
    dp["bg_manager_factory"] = bg_manager_factory
    _setup_outer_middlewares(dp=dp, config=config)
    _setup_inner_middlewares(dp=dp)

    engine: AsyncEngine = dp["engine"]
    dp["data_store"] = SQLAlchemyDataStore(engine, schema=Base.metadata.schema)
    dp["event_broker"] = AsyncpgEventBroker.from_async_sqla_engine(engine)

    return dp
