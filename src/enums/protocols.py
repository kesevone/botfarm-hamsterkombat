from enum import StrEnum


class ProxyProtocol(StrEnum):
    HTTP = "http"
    SOCKS4 = "socks4"
    SOCKS5 = "socks5"
