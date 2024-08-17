import time
from http import HTTPMethod
from typing import Any, Optional

from aiohttp_socks import ProxyConnector
from fake_useragent import UserAgent

from src.hamster.api.client import HamsterClient
from src.hamster.api.fingerprint import generate_fingerprint
from src.hamster.enums import AuthEndpoints, ClickerEndpoints
from src.hamster.models import (
    AuthData,
    HamsterBoost,
    HamsterBoosts,
    HamsterConfig,
    HamsterDailyCipher,
    HamsterData,
    HamsterTask,
    HamsterTasks,
    HamsterUpgrades,
    UserData,
)
from src.hamster.models.hamster_data import HamsterDailyCombo, HamsterIPData


class HamsterKombat(HamsterClient):
    proxy_connector: Optional[ProxyConnector]

    __slots__ = ("proxy_connector",)

    def __init__(
        self,
        base_url: str,
        headers: Optional[dict] = None,
    ) -> None:
        super().__init__(base_url=base_url, headers=headers)

        self.proxy_connector = None

    def set_proxy(self, proxy_connector: ProxyConnector) -> None:
        self.proxy_connector = proxy_connector

    async def auth_telegram(
        self,
        bearer_token: str,
        endpoint: Optional[AuthEndpoints] = AuthEndpoints.TELEGRAM,
    ) -> Optional[UserData]:
        self.headers["Authorization"] = f"Bearer {bearer_token}"
        user_agent = UserAgent(
            browsers=["chrome"],
            os=["android", "ios"],
            platforms=["mobile", "tablet"],
        )
        self.headers["User-Agent"] = str(user_agent.random)
        response: Optional[dict] = await self._make_request(
            method=HTTPMethod.POST,
            endpoint=endpoint,
            proxy_connector=self.proxy_connector,
        )
        return UserData(**response.get("telegramUser"))

    async def auth_webapp(
        self,
        webapp_data: str,
        endpoint: Optional[AuthEndpoints] = AuthEndpoints.WEBAPP,
    ) -> Optional[AuthData]:
        json: dict[str, Any] = {
            "fingerprint": generate_fingerprint(),
            "initDataRaw": webapp_data,
        }
        self.headers["Authorization"] = f"authToken is empty, store token null"
        user_agent = UserAgent(
            browsers=["chrome"],
            os=["android", "ios"],
            platforms=["mobile", "tablet"],
        )
        self.headers["User-Agent"] = str(user_agent.random)
        response: Optional[dict] = await self._make_request(
            method=HTTPMethod.POST,
            endpoint=endpoint,
            json=json,
            proxy_connector=self.proxy_connector,
        )
        return AuthData(**response)

    async def ip(
        self,
        bearer_token: str,
        endpoint: Optional[AuthEndpoints] = AuthEndpoints.IP,
    ) -> Optional[HamsterIPData]:
        self.headers["Authorization"] = f"Bearer {bearer_token}"
        user_agent = UserAgent(
            browsers=["chrome"],
            os=["android", "ios"],
            platforms=["mobile", "tablet"],
        )
        self.headers["User-Agent"] = str(user_agent.random)
        response: Optional[dict] = await self._make_request(
            method=HTTPMethod.GET,
            endpoint=endpoint,
            proxy_connector=self.proxy_connector,
        )
        return HamsterIPData(**response)

    async def sync(
        self,
        bearer_token: str,
        endpoint: ClickerEndpoints = ClickerEndpoints.SYNC,
    ) -> Optional[HamsterData]:
        self.headers["Authorization"] = f"Bearer {bearer_token}"
        user_agent = UserAgent(
            browsers=["chrome"],
            os=["android", "ios"],
            platforms=["mobile", "tablet"],
        )
        self.headers["User-Agent"] = str(user_agent.random)
        response: Optional[dict] = await self._make_request(
            method=HTTPMethod.POST,
            endpoint=endpoint,
            proxy_connector=self.proxy_connector,
        )
        return HamsterData(**response.get("clickerUser"))

    async def buy_upgrade(
        self,
        bearer_token: str,
        upgrade_id: str,
        endpoint: ClickerEndpoints = ClickerEndpoints.BUY_UPGRADE,
    ) -> Optional[HamsterData]:
        self.headers["Accept"] = "application/json"
        self.headers["Authorization"] = f"Bearer {bearer_token}"
        user_agent = UserAgent(
            browsers=["chrome"],
            os=["android", "ios"],
            platforms=["mobile", "tablet"],
        )
        self.headers["User-Agent"] = str(user_agent.random)
        json: dict[str, Any] = {
            "upgradeId": upgrade_id,
            "timestamp": int(time.time()),
        }
        response: Optional[dict] = await self._make_request(
            method=HTTPMethod.POST,
            endpoint=endpoint,
            json=json,
            proxy_connector=self.proxy_connector,
        )

        return HamsterData(**response.get("clickerUser"))

    async def tap(
        self,
        bearer_token: str,
        available_taps: int,
        count: int,
        endpoint: ClickerEndpoints = ClickerEndpoints.TAP,
    ) -> Optional[HamsterData]:
        self.headers["Accept"] = "application/json"
        self.headers["Authorization"] = f"Bearer {bearer_token}"
        user_agent = UserAgent(
            browsers=["chrome"],
            os=["android", "ios"],
            platforms=["mobile", "tablet"],
        )
        self.headers["User-Agent"] = str(user_agent.random)
        json: dict[str, Any] = {
            "availableTaps": available_taps,
            "count": count,
            "timestamp": int(time.time()),
        }
        response: Optional[dict] = await self._make_request(
            method=HTTPMethod.POST,
            endpoint=endpoint,
            json=json,
            proxy_connector=self.proxy_connector,
        )
        return HamsterData(**response.get("clickerUser"))

    async def get_config(
        self,
        bearer_token: str,
        endpoint: ClickerEndpoints = ClickerEndpoints.CONFIG,
    ) -> HamsterConfig:
        self.headers["Authorization"] = f"Bearer {bearer_token}"
        user_agent = UserAgent(
            browsers=["chrome"],
            os=["android", "ios"],
            platforms=["mobile", "tablet"],
        )
        self.headers["User-Agent"] = str(user_agent.random)
        response: Optional[dict] = await self._make_request(
            method=HTTPMethod.POST,
            endpoint=endpoint,
            proxy_connector=self.proxy_connector,
        )
        return HamsterConfig(**response)

    async def get_boosts(
        self,
        bearer_token: str,
        endpoint: ClickerEndpoints = ClickerEndpoints.BOOSTS,
    ) -> Optional[HamsterBoosts]:
        self.headers["Authorization"] = f"Bearer {bearer_token}"
        user_agent = UserAgent(
            browsers=["chrome"],
            os=["android", "ios"],
            platforms=["mobile", "tablet"],
        )
        self.headers["User-Agent"] = str(user_agent.random)
        response: Optional[dict] = await self._make_request(
            method=HTTPMethod.POST,
            endpoint=endpoint,
            proxy_connector=self.proxy_connector,
        )
        return HamsterBoosts(
            boosts=[HamsterBoost(**boost) for boost in response.get("boostsForBuy")]
        )

    async def get_upgrades(
        self,
        bearer_token: str,
        endpoint: ClickerEndpoints = ClickerEndpoints.UPGRADES,
    ) -> Optional[HamsterUpgrades]:
        self.headers["Authorization"] = f"Bearer {bearer_token}"
        user_agent = UserAgent(
            browsers=["chrome"],
            os=["android", "ios"],
            platforms=["mobile", "tablet"],
        )
        self.headers["User-Agent"] = str(user_agent.random)
        response: Optional[dict] = await self._make_request(
            method=HTTPMethod.POST,
            endpoint=endpoint,
            proxy_connector=self.proxy_connector,
        )
        return HamsterUpgrades(**response)

    async def get_tasks(
        self,
        bearer_token: str,
        endpoint: ClickerEndpoints = ClickerEndpoints.TASKS,
    ) -> Optional[HamsterTasks]:
        self.headers["Authorization"] = f"Bearer {bearer_token}"
        user_agent = UserAgent(
            browsers=["chrome"],
            os=["android", "ios"],
            platforms=["mobile", "tablet"],
        )
        self.headers["User-Agent"] = str(user_agent.random)
        response: Optional[dict] = await self._make_request(
            method=HTTPMethod.POST,
            endpoint=endpoint,
            proxy_connector=self.proxy_connector,
        )
        return HamsterTasks(
            tasks=[HamsterTask(**task) for task in response.get("tasks")]
        )

    async def buy_boost(
        self,
        bearer_token: str,
        boost_id: str,
        endpoint: ClickerEndpoints = ClickerEndpoints.BUY_BOOST,
    ) -> Optional[HamsterData]:
        self.headers["Accept"] = "application/json"
        self.headers["Authorization"] = f"Bearer {bearer_token}"
        user_agent = UserAgent(
            browsers=["chrome"],
            os=["android", "ios"],
            platforms=["mobile", "tablet"],
        )
        self.headers["User-Agent"] = str(user_agent.random)
        json: dict[str, Any] = {
            "boostId": boost_id,
            "timestamp": int(time.time()),
        }
        response: Optional[dict] = await self._make_request(
            method=HTTPMethod.POST,
            endpoint=endpoint,
            json=json,
            proxy_connector=self.proxy_connector,
        )
        return HamsterData(**response.get("clickerUser"))

    async def claim_daily_cipher(
        self,
        bearer_token: str,
        cipher: str,
        endpoint: ClickerEndpoints = ClickerEndpoints.CLAIM_DAILY_CIPHER,
    ) -> tuple[Optional[HamsterData], Optional[HamsterDailyCipher]]:
        self.headers["Authorization"] = f"Bearer {bearer_token}"
        user_agent = UserAgent(
            browsers=["chrome"],
            os=["android", "ios"],
            platforms=["mobile", "tablet"],
        )
        self.headers["User-Agent"] = str(user_agent.random)
        json: dict[str, Any] = {
            "cipher": cipher,
        }
        response: Optional[dict] = await self._make_request(
            method=HTTPMethod.POST,
            endpoint=endpoint,
            json=json,
            proxy_connector=self.proxy_connector,
        )
        return HamsterData(**response.get("clickerUser")), HamsterDailyCipher(
            **response.get("dailyCipher")
        )

    async def claim_daily_combo(
        self,
        bearer_token: str,
        endpoint: ClickerEndpoints = ClickerEndpoints.CLAIM_DAILY_COMBO,
    ) -> Optional[HamsterData]:
        self.headers["Authorization"] = f"Bearer {bearer_token}"
        user_agent = UserAgent(
            browsers=["chrome"],
            os=["android", "ios"],
            platforms=["mobile", "tablet"],
        )
        self.headers["User-Agent"] = str(user_agent.random)
        response: Optional[dict] = await self._make_request(
            method=HTTPMethod.POST,
            endpoint=endpoint,
            proxy_connector=self.proxy_connector,
        )
        return HamsterData(**response.get("clickerUser"))

    async def check_task(
        self,
        bearer_token: str,
        task_id: str,
        endpoint: ClickerEndpoints = ClickerEndpoints.CHECK_TASK,
    ) -> tuple[Optional[HamsterTask], Optional[HamsterData]]:
        self.headers["Authorization"] = f"Bearer {bearer_token}"
        user_agent = UserAgent(
            browsers=["chrome"],
            os=["android", "ios"],
            platforms=["mobile", "tablet"],
        )
        self.headers["User-Agent"] = str(user_agent.random)
        json: dict[str, Any] = {
            "taskId": task_id,
        }
        response: Optional[dict] = await self._make_request(
            method=HTTPMethod.POST,
            endpoint=endpoint,
            json=json,
            proxy_connector=self.proxy_connector,
        )
        return HamsterTask(**response.get("task")), HamsterData(
            **response.get("clickerUser")
        )

    async def get_actual_combos(self) -> Optional[HamsterDailyCombo]:
        response: Optional[dict] = await self._make_request_to_other(
            method=HTTPMethod.GET,
            base_url="https://api21.datavibe.top",
            endpoint="/api/GetCombo",
            proxy_connector=self.proxy_connector,
        )
        return HamsterDailyCombo(
            upgradeIds=response.get("combo"), date=response.get("date")
        )
