from __future__ import annotations

from typing import Optional

from apscheduler import AsyncScheduler
from apscheduler.datastores.sqlalchemy import SQLAlchemyDataStore
from apscheduler.eventbrokers.asyncpg import AsyncpgEventBroker
from pydantic import BaseModel, SecretStr
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict
from redis.asyncio import ConnectionPool, Redis
from sqlalchemy import URL
from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    AsyncEngine,
    AsyncSession,
    create_async_engine,
)

from src.database import Base


class _BaseSettings(BaseSettings):
    model_config = SettingsConfigDict(
        extra="ignore", env_file="../.env", env_file_encoding="utf-8"
    )


class CommonConfig(_BaseSettings, env_prefix="COMMON_"):
    bot_token: SecretStr
    develop_id: int
    server_ip: str
    drop_pending_updates: bool
    sqlalchemy_logging: bool
    sessions_path: str


class HamsterConfig(_BaseSettings, env_prefix="HAMSTER_"):
    base_url: str


class PostgresConfig(_BaseSettings, env_prefix="POSTGRES_"):
    host: str
    port: int
    db: str
    user: str
    password: SecretStr

    def build_dsn(self) -> URL:
        return URL.create(
            drivername="postgresql+asyncpg",
            username=self.user,
            password=self.password.get_secret_value(),
            host=self.host,
            port=self.port,
            database=self.db,
        )

    def create_pool(
        self, dsn: Optional[str | URL] = None, enable_logging: bool = False
    ) -> tuple[AsyncEngine, async_sessionmaker[AsyncSession]]:
        if not dsn:
            dsn = self.build_dsn()

        engine: AsyncEngine = create_async_engine(url=dsn, echo=enable_logging)
        return engine, async_sessionmaker(engine, expire_on_commit=False)

    @staticmethod
    def build_scheduler(engine: AsyncEngine) -> AsyncScheduler:
        data_store = SQLAlchemyDataStore(
            engine_or_url=engine, schema=Base.metadata.schema
        )
        event_broker = AsyncpgEventBroker.from_async_sqla_engine(engine)
        return AsyncScheduler(
            data_store=data_store, event_broker=event_broker, identity="schd"
        )


class RedisConfig(_BaseSettings, env_prefix="REDIS_"):
    host: str
    port: int
    db: int

    def build_client(self) -> Redis:
        return Redis(
            connection_pool=ConnectionPool(
                host=self.host,
                port=self.port,
                db=self.db,
            )
        )


class AppConfig(BaseModel):
    common: CommonConfig
    hamster: HamsterConfig
    postgres: PostgresConfig
    redis: RedisConfig

    @classmethod
    def create(cls) -> AppConfig:
        return cls(
            common=CommonConfig(),
            hamster=HamsterConfig(),
            postgres=PostgresConfig(),
            redis=RedisConfig(),
        )
