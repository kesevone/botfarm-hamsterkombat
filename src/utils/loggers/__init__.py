import logging

from .multiline import MultilineLogger

__all__ = [
    "database",
    "service",
    "log_autofarm",
    "log_autoupgrade",
    "log_autosync",
    "setup_logger",
    "MultilineLogger",
    "log_hamster",
]

database: logging.Logger = logging.getLogger("bot.database")
service: logging.Logger = logging.getLogger("bot.services")
log_hamster: logging.Logger = logging.getLogger("api.hamster")
log_autofarm: logging.Logger = logging.getLogger("hamster.autofarm")
log_autoupgrade: logging.Logger = logging.getLogger("hamster.autoupgrade")
log_autosync: logging.Logger = logging.getLogger("hamster.autosync")


def setup_logger(level: int = logging.INFO) -> None:
    for name in ["aiogram.middlewares", "aiogram.event", "aiohttp.access"]:
        logging.getLogger(name).setLevel(logging.WARNING)

    for name in ["apscheduler.executors.default"]:
        logging.getLogger(name).propagate = False

    logging.basicConfig(
        format="[%(asctime)s] [%(levelname)s] | [%(name)s] — %(message)s",
        datefmt="%H:%M:%S",
        level=level,
    )
