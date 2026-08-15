"""Proxy rotation and management.

Smart proxy system:
- Auto-generates DataImpulse sticky proxies if proxies.txt is empty
- Port-based sticky IPs (10000-20000)
- Health tracking with cooldown
- Country detection support
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .detect import detect_proxy_country, ProxyInfo

log = logging.getLogger(__name__)


@dataclass
class ProxyEntry:
    raw: str
    url: str
    username: str = ""
    password: str = ""
    host: str = ""
    port: int = 0
    country_code: str = ""
    country_name: str = ""
    latency_factor: float = 1.2
    last_used: float = 0.0
    fail_count: int = 0


class ProxyManager:
    """Proxy rotation with health tracking.

    Smart features:
    - Auto-generates DataImpulse sticky proxies from credentials
    - Port-based sticky IPs (each port = unique IP)
    - Round-robin with health check
    - Cooldown management
    """

    def __init__(
        self,
        proxy_file: Optional[str] = None,
        static_proxy: Optional[str] = None,
        cooldown: int = 30,
    ):
        self._entries: list[ProxyEntry] = []
        self._cooldown = cooldown
        self._index = 0

        if static_proxy:
            self._entries.append(self._parse_line(static_proxy))
        elif proxy_file:
            self._load_file(proxy_file)

        # Smart: auto-generate DataImpulse proxies if empty
        if not self._entries:
            self._auto_generate_dataimpulse()

    def _auto_generate_dataimpulse(self) -> None:
        """Auto-generate DataImpulse sticky proxies from env vars."""
        username = os.getenv("PROXY_USERNAME", "")
        password = os.getenv("PROXY_PASSWORD", "")
        host = os.getenv("PROXY_HOST", "gw.dataimpulse.com")
        port_start = int(os.getenv("PROXY_PORT_START", "10000"))
        port_end = int(os.getenv("PROXY_PORT_END", "20000"))

        if not username or not password:
            log.debug("No DataImpulse credentials, skipping auto-generation")
            return

        log.info(
            "Auto-generating DataImpulse sticky proxies: %s@%s:%d-%d",
            username, host, port_start, port_end,
        )

        for port in range(port_start, port_end + 1):
            url = f"http://{username}:{password}@{host}:{port}"
            entry = ProxyEntry(
                raw=url,
                url=url,
                username=username,
                password=password,
                host=host,
                port=port,
            )
            self._entries.append(entry)

        log.info("Generated %d DataImpulse sticky proxies", len(self._entries))

    def _load_file(self, path: str) -> None:
        """Load proxies from file."""
        file_path = Path(path)
        if not file_path.exists():
            log.warning("Proxy file not found: %s", path)
            return

        for line in file_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            try:
                entry = self._parse_line(line)
                self._entries.append(entry)
            except Exception as exc:
                log.debug("Skipping invalid proxy line: %s (%s)", line[:30], exc)

        log.info("Loaded %d proxies from %s", len(self._entries), path)

    def _parse_line(self, line: str) -> ProxyEntry:
        """Parse proxy line in multiple formats.

        Supported formats:
        1. hostname:port:login:password
        2. hostname:port@login:password
        3. login:password@hostname:port
        4. protocol://login:password@hostname:port
        5. login:password:hostname:port
        6. hostname:port
        """
        country_name = ""
        if "|" in line:
            line, country_name = line.split("|", 1)
            country_name = country_name.strip()

        url = line
        username = ""
        password = ""
        host = ""
        port = 0
        protocol = ""

        # Extract protocol if present
        if "://" in url:
            protocol, rest = url.split("://", 1)
        else:
            rest = url

        # Extract credentials if @ present (formats 2, 3, 4)
        if "@" in rest:
            left, right = rest.split("@", 1)
            # Determine which side has host:port
            right_parts = right.split(":")
            if len(right_parts) == 2:
                try:
                    int(right_parts[1])
                    # Right side is host:port -> format 3/4
                    username, password = left.split(":", 1) if ":" in left else (left, "")
                    rest = right
                except ValueError:
                    # Right side not host:port -> format 2
                    rest = left
                    username, password = right.split(":", 1) if ":" in right else (right, "")
            else:
                # Default: left is creds, right is host:port
                username, password = left.split(":", 1) if ":" in left else (left, "")
                rest = right

        # Parse host:port from remaining part
        parts = rest.split(":")
        if len(parts) >= 2:
            host = parts[0]
            try:
                port = int(parts[1])
            except ValueError:
                pass
        elif len(parts) == 1:
            host = parts[0]

        # For formats without @, detect credentials in host:port:login:password
        if not username and len(parts) == 4:
            try:
                int(parts[1])
                # Format 1: hostname:port:login:password
                host = parts[0]
                port = int(parts[1])
                username = parts[2]
                password = parts[3]
            except ValueError:
                # Format 5: login:password:hostname:port
                username = parts[0]
                password = parts[1]
                host = parts[2]
                try:
                    port = int(parts[3])
                except ValueError:
                    pass

        # Build normalized URL
        if protocol and host:
            if username and password:
                url = f"{protocol}://{username}:{password}@{host}:{port}"
            elif host:
                url = f"{protocol}://{host}:{port}"

        return ProxyEntry(
            raw=line,
            url=url,
            username=username,
            password=password,
            host=host,
            port=port,
            country_code=country_name[:2].upper() if country_name else "",
            country_name=country_name,
        )

    def next(self) -> Optional[str]:
        """Get next available proxy (round-robin with health check)."""
        if not self._entries:
            return None

        now = time.time()
        available = [
            e for e in self._entries
            if now - e.last_used >= self._cooldown and e.fail_count < 3
        ]

        if not available:
            # Reset fail counts if all are exhausted
            if all(e.fail_count >= 3 for e in self._entries):
                for e in self._entries:
                    e.fail_count = 0
                available = self._entries
            else:
                return None

        entry = available[self._index % len(available)]
        self._index += 1
        entry.last_used = now
        return entry.url

    def mark_failed(self, proxy_url: str) -> None:
        """Mark a proxy as failed."""
        for entry in self._entries:
            if entry.url == proxy_url:
                entry.fail_count += 1
                log.debug("Proxy marked failed: %s (count=%d)", proxy_url[:30], entry.fail_count)
                break

    def detect_country(self, proxy_url: Optional[str] = None) -> ProxyInfo:
        """Detect country for a proxy."""
        return detect_proxy_country(proxy_url)

    @property
    def count(self) -> int:
        return len(self._entries)

    @property
    def available(self) -> int:
        now = time.time()
        return sum(
            1 for e in self._entries
            if now - e.last_used >= self._cooldown and e.fail_count < 3
        )
