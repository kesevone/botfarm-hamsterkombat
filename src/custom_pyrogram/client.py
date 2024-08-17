from pyrogram import Client
from pyrogram.session import Auth


class CustomClient(Client):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def load_session(self):
        await self.storage.open()
        session_empty = any(
            [
                await self.storage.test_mode() is None,
                await self.storage.auth_key() is None,
                await self.storage.user_id() is None,
                await self.storage.is_bot() is None,
            ]
        )

        if session_empty:
            if not self.api_id or not self.api_hash:
                raise AttributeError(
                    "The API key is required for new authorizations. "
                    "More info: https://docs.pyrogram.org/start/auth"
                )

            await self.storage.api_id(self.api_id)

            await self.storage.dc_id(2)
            await self.storage.date(0)

            await self.storage.test_mode(self.test_mode)
            await self.storage.auth_key(
                await Auth(
                    self, await self.storage.dc_id(), await self.storage.test_mode()
                ).create()
            )
            await self.storage.user_id(None)
            await self.storage.is_bot(None)
        else:
            if not await self.storage.api_id():
                if self.api_id:
                    await self.storage.api_id(self.api_id)
                else:
                    raise AttributeError("API ID is required")
