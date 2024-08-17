from aiogram.fsm.state import State, StatesGroup


class GeneralDialog(StatesGroup):
    WELCOME = State()


class AccountDialog(StatesGroup):
    INFO = State()


class AccountBoostsDialog(StatesGroup):
    SELECT_BOOST = State()
    INFO = State()


class AccountUpgradesDialog(StatesGroup):
    SELECT_UPGRADE = State()


class AccountUpgradeDialog(StatesGroup):
    INFO = State()


class AccountCreatorDialog(StatesGroup):
    SELECT_AUTH_TYPE = State()
    INPUT_PROXY_DATA = State()
    BEARER_TOKEN = State()
    WEBAPP_DATA = State()
    SESSION = State()


class AccountConfigsDialog(StatesGroup):
    SELECT_CONFIG = State()


class AccountConfigDialog(StatesGroup):
    INFO = State()
    AUTOUPGRADE_LIMIT = State()


class AccountConfigAutofarmDialog(StatesGroup):
    INFO = State()


class AccountConfigAutoupgradeDialog(StatesGroup):
    INFO = State()


class AccountConfigAutosyncDialog(StatesGroup):
    INFO = State()


class AccountConfigProxyDialog(StatesGroup):
    INFO = State()
    INPUT_TIMEOUT_SECONDS = State()
    INPUT_PROXY_DATA = State()


class SubscriptionPlansDialog(StatesGroup):
    SELECT_PLAN = State()
