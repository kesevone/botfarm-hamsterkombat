import asyncio

from aiogram import Bot, Dispatcher

from src.app_config import AppConfig
from src.factory import create_bot, create_dispatcher
from src.runners import run_polling
from src.utils.loggers import setup_logger


async def main() -> None:
    setup_logger()
    config: AppConfig = AppConfig.create()
    bot: Bot = create_bot(config=config)
    dp: Dispatcher = await create_dispatcher(config=config)
    return await run_polling(dp=dp, bot=bot)


if __name__ == "__main__":
    asyncio.run(main())
