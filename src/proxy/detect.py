"""Proxy country/latency detection."""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass
from typing import Optional

import requests

log = logging.getLogger(__name__)

IP_API_URL = os.getenv("IP_API_URL", "http://ip-api.com/json")
IPINFO_URL = os.getenv("IPINFO_URL", "https://ipinfo.io/json")


@dataclass
class ProxyInfo:
    country_code: str = "US"
    country_name: str = ""
    latency_ms: float = 0.0
    latency_factor: float = 1.0
    ip: str = ""


def detect_proxy_country(proxy_url: Optional[str] = None) -> ProxyInfo:
    """Detect proxy country and measure latency."""
    proxies = None
    if proxy_url:
        proxies = {"http": proxy_url, "https": proxy_url}

    # Try ip-api.com first
    info = _try_ip_api(proxies)
    if info:
        return info

    # Fallback to ipinfo.io
    info = _try_ipinfo(proxies)
    if info:
        return info

    log.warning("Could not detect proxy country, defaulting to US")
    return ProxyInfo(country_code="US", latency_ms=3000, latency_factor=2.0)


def _try_ip_api(proxies: Optional[dict] = None) -> Optional[ProxyInfo]:
    try:
        start = time.time()
        resp = requests.get(
            IP_API_URL,
            params={"fields": "status,country,countryCode,query"},
            proxies=proxies,
            timeout=5,
        )
        latency = (time.time() - start) * 1000

        if resp.status_code == 200:
            data = resp.json()
            if data.get("status") == "success":
                return ProxyInfo(
                    country_code=data.get("countryCode", "US"),
                    country_name=data.get("country", ""),
                    latency_ms=latency,
                    latency_factor=_calc_factor(latency),
                    ip=data.get("query", ""),
                )
    except Exception as exc:
        log.debug("ip-api detection failed: %s", exc)
    return None


def _try_ipinfo(proxies: Optional[dict] = None) -> Optional[ProxyInfo]:
    try:
        start = time.time()
        resp = requests.get(IPINFO_URL, proxies=proxies, timeout=5)
        latency = (time.time() - start) * 1000

        if resp.status_code == 200:
            data = resp.json()
            country = data.get("country", "US")
            return ProxyInfo(
                country_code=country[:2].upper(),
                country_name=country,
                latency_ms=latency,
                latency_factor=_calc_factor(latency),
                ip=data.get("ip", ""),
            )
    except Exception as exc:
        log.debug("ipinfo detection failed: %s", exc)
    return None


def _calc_factor(latency_ms: float) -> float:
    """Calculate speed factor based on latency."""
    if latency_ms < 1200:
        return 1.0
    elif latency_ms < 3000:
        return 1.5
    else:
        return 2.5
