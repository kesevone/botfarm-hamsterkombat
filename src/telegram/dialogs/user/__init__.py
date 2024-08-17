from aiogram import F, Router
from aiogram.enums import ChatType

from .accounts import (
    account_boosts_dialog,
    account_creator_dialog,
    account_dialog,
    account_upgrade_dialog,
    account_upgrades_dialog,
)
from .configs import (
    account_autofarm_config_dialog,
    account_autosync_config_dialog,
    account_autoupgrade_config_dialog,
    account_config_dialog,
    account_configs_dialog,
    account_proxy_config_dialog,
)
from .general import general_dialog, handlers

router = Router(name=__name__)
router.include_routers(
    handlers.user_router,
    handlers.admin_router,
    general_dialog,
    account_dialog,
    account_creator_dialog,
    account_boosts_dialog,
    account_upgrades_dialog,
    account_upgrade_dialog,
    account_configs_dialog,
    account_autofarm_config_dialog,
    account_autoupgrade_config_dialog,
    account_autosync_config_dialog,
    account_proxy_config_dialog,
    account_config_dialog,
)
router.message.filter(F.chat.type == ChatType.PRIVATE)
