from typing import Dict

from aiogram import Bot
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.common import WhenCondition
from aiogram_dialog.widgets.text import Text
from aiogram_dialog.widgets.text.jinja import default_env, JINJA_ENV_FIELD
from jinja2 import Environment


class InternalJinja(Text):
    def __init__(self, text: str, when: WhenCondition = None):
        super().__init__(when=when)
        self.template_text = text

    async def _render_text(
        self,
        data: Dict,
        manager: DialogManager,
    ) -> str:
        if JINJA_ENV_FIELD in manager.dialog_data:
            env = manager.dialog_data[JINJA_ENV_FIELD]
        else:
            bot: Bot = manager.middleware_data.get("bot")
            env: Environment = getattr(bot, JINJA_ENV_FIELD, default_env)

        template = env.get_template(self.template_text)
        template_text: str = template.render(data)
        internal_template = env.get_template(template_text)

        if env.is_async:
            return await internal_template.render_async(data)
        else:
            return internal_template.render(data)
