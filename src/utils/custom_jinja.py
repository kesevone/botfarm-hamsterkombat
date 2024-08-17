from typing import Any, Optional

from jinja2 import Environment, Template


class CustomJinja:
    """
    A class for rendering CustomJinja templates.

    Args:
        text (str): The CustomJinja template text.
        trim_blocks (bool, optional): Whether to trim the blocks. Defaults to True.
        lstrip_blocks (bool, optional): Whether to lstrip the blocks. Defaults to True.
        autoescape (bool, optional)
        kwargs (Any, optional): The keyword arguments to pass to the template.
    """

    def __init__(
        self,
        text: str,
        trim_blocks: Optional[bool] = True,
        lstrip_blocks: Optional[bool] = True,
        autoescape: Optional[bool] = True,
        **kwargs: Any,
    ) -> None:
        self.kwargs = kwargs
        self.text = text
        self.jinja_env = Environment(
            trim_blocks=trim_blocks,
            lstrip_blocks=lstrip_blocks,
            enable_async=True,
            autoescape=autoescape,
        )

    async def render(self) -> str:
        """
        Render the CustomJinja template.

        Returns:
            str: The rendered template text.
        """

        template: Template = self.jinja_env.from_string(self.text)
        if not self.kwargs:
            return await template.render_async()
        return await template.render_async(self.kwargs)
