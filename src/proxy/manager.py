"""Proxy rotation and management."""

from __future__ import annotations

import logging
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
    """Proxy rotation with health tracking."""

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

    def _load_file(self, path: str) -> None:
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
            # Format 3/4: user:pass@host:port (right has 2 parts, second is numeric)
            # Format 2: host:port@user:pass (left has 2 parts, second is numeric)
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
        """Get next available proxy (round-robin)."""
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
