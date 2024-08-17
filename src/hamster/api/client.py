from http import HTTPMethod
from typing import Any, Optional

import aiohttp
from aiohttp import ClientConnectionError
from aiohttp_socks import ProxyConnector
from python_socks import ProxyConnectionError, ProxyError

from src.hamster.enums import AuthEndpoints
from src.hamster.exceptions import RequestError
from src.utils.loggers import log_hamster


class HamsterClient(object):
    def __init__(
        self,
        base_url: str,
        headers: Optional[dict] = None,
    ):
        self.base_url = base_url
        self.headers: Optional[dict] = headers

        if not headers:
            self.headers = {
                "Connection": "keep-alive",
                "Accept": "*/*",
                "Accept-Encoding": "gzip, deflate, br, zstd",
                "Accept-Language": "ru,en;q=0.9,en-GB;q=0.8,en-US;q=0.7",
                "Authorization": "",
                "Origin": "https://api.hamsterkombatgame.io",
                "Referer": "https://api.hamsterkombatgame.io/",
                "sec-ch-ua": '"Chromium";v="122", "Not(A:Brand";v="24", "Android WebView";v="122"',
                "sec-ch-ua-mobile": "?1",
                "X-Requested-With": "org.telegram.messenger",
                "X" "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-site",
            }

    @staticmethod
    async def check_proxy(
        proxy_connector: ProxyConnector,
        real_ip: str,
        response_timeout: Optional[int] = 10,
    ) -> bool:
        judges = [
            "http://azenv.net/",
            "http://httpheader.net/azenv.php",
            "http://mojeip.net.pl/asdfa/azenv.php",
        ]

        for judge in judges:
            try:
                async with aiohttp.ClientSession(
                    connector=proxy_connector, connector_owner=False
                ) as client:
                    async with client.get(judge, timeout=response_timeout) as response:
                        text = await response.text()
                        return response.ok and real_ip not in text
            except (
                ClientConnectionError,
                ConnectionResetError,
                ProxyConnectionError,
                TimeoutError,
                ProxyError,
            ):
                log_hamster.info(
                    "Proxy is unavailable: %s | %s",
                    judge,
                    proxy_connector.proxy_host,
                )
                continue
        return False

    async def _make_request(
        self,
        method: HTTPMethod,
        endpoint: AuthEndpoints,
        proxy_connector: ProxyConnector,
        **kwargs: Any,
    ) -> Optional[dict]:
        async with aiohttp.ClientSession(
            base_url=self.base_url,
            headers=self.headers,
            connector=proxy_connector,
            connector_owner=False,
        ) as client:
            async with client.request(method, endpoint, **kwargs) as response:
                if not response.ok:
                    raise RequestError(
                        f"Cannot make request to Hamster API: {endpoint} | {response.status} | {await response.text()}"
                    )

                log_hamster.info(
                    "Request to Hamster API: %s | %s",
                    endpoint,
                    proxy_connector.proxy_host,
                )

                return await response.json()

    @staticmethod
    async def _make_request_to_other(
        method: HTTPMethod,
        base_url: str,
        endpoint: str,
        proxy_connector: Optional[ProxyConnector] = None,
        **kwargs: Any,
    ) -> Optional[dict]:
        async with aiohttp.ClientSession(
            base_url=base_url, connector=proxy_connector, connector_owner=False
        ) as session:
            async with session.request(method, endpoint, **kwargs) as response:
                if not response.ok:
                    raise RequestError(
                        f"Cannot make request to {base_url}: {endpoint} | {response.status} | {await response.text()}"
                    )

                log_hamster.info(
                    "Request to Unknown API: %s | %s",
                    endpoint,
                    proxy_connector.proxy_host,
                )

                return await response.json()
