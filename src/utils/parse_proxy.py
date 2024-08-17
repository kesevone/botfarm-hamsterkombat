import re
from typing import Optional

from pydantic import BaseModel

from src.enums import ProxyProtocol


class ProxyData(BaseModel):
    protocol: ProxyProtocol
    host: str
    port: int
    username: str
    password: str

    @property
    def url(self):
        return (
            f"{self.protocol}://{self.username}:{self.password}@{self.host}:{self.port}"
        )


def parse_proxy_from_string(proxy: str) -> Optional[ProxyData]:
    regex = r"^(\w+):\/\/(\w+):(\w+)@([\w.-]+):(\d+)$"
    match = re.match(regex, proxy)

    if match and proxy.startswith(
        (ProxyProtocol.HTTP, ProxyProtocol.SOCKS4, ProxyProtocol.SOCKS5)
    ):
        protocol: str = match.group(1)
        username: str = match.group(2)
        password: str = match.group(3)
        host: str = match.group(4)
        port: int = int(match.group(5))
        return ProxyData(
            protocol=ProxyProtocol(protocol),
            host=host,
            port=port,
            username=username,
            password=password,
        )
