"""Smart proxy rotation with sticky sessions.

Features:
- Auto-generate DataImpulse sticky proxies
- Smart rotation (latency + health based)
- Sticky session (same proxy per signup flow)
- Retry with different proxy on failure
- Health priority (healthy proxies first)
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass
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
    success_count: int = 0
    total_uses: int = 0

    @property
    def health_score(self) -> float:
        """Health score: higher = healthier."""
        if self.total_uses == 0:
            return 1.0  # Untested = neutral
        success_rate = self.success_count / self.total_uses
        fail_penalty = self.fail_count * 0.3
        return max(0.0, success_rate - fail_penalty)

    @property
    def is_healthy(self) -> bool:
        return self.fail_count < 3 and self.health_score > 0.3


class ProxyManager:
    """Smart proxy rotation with sticky sessions.

    Features:
    - Auto-generates DataImpulse sticky proxies from credentials
    - Port-based sticky IPs (each port = unique IP)
    - Smart rotation: health + latency based
    - Sticky sessions: same proxy for entire signup flow
    - Retry with different proxy on failure
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

        # Sticky session tracking
        self._sticky_sessions: dict[str, ProxyEntry] = {}  # session_id -> proxy
        self._sticky_ttl: dict[str, float] = {}  # session_id -> expiry

        if static_proxy:
            self._entries.append(self._parse_line(static_proxy))
        elif proxy_file:
            self._load_file(proxy_file)

        # Auto-generate DataImpulse proxies if empty
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
        from pathlib import Path
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
        """Parse proxy line in multiple formats."""
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

        # Extract credentials if @ present
        if "@" in rest:
            left, right = rest.split("@", 1)
            right_parts = right.split(":")
            if len(right_parts) == 2:
                try:
                    int(right_parts[1])
                    username, password = left.split(":", 1) if ":" in left else (left, "")
                    rest = right
                except ValueError:
                    rest = left
                    username, password = right.split(":", 1) if ":" in right else (right, "")
            else:
                username, password = left.split(":", 1) if ":" in left else (left, "")
                rest = right

        # Parse host:port
        parts = rest.split(":")
        if len(parts) >= 2:
            host = parts[0]
            try:
                port = int(parts[1])
            except ValueError:
                pass
        elif len(parts) == 1:
            host = parts[0]

        if not username and len(parts) == 4:
            try:
                int(parts[1])
                host = parts[0]
                port = int(parts[1])
                username = parts[2]
                password = parts[3]
            except ValueError:
                username = parts[0]
                password = parts[1]
                host = parts[2]
                try:
                    port = int(parts[3])
                except ValueError:
                    pass

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

    # ------------------------------------------------------------------ #
    # Smart rotation
    # ------------------------------------------------------------------ #

    def _get_available(self, exclude: Optional[set[str]] = None) -> list[ProxyEntry]:
        """Get available proxies, sorted by health + latency."""
        now = time.time()
        exclude = exclude or set()

        available = [
            e for e in self._entries
            if e.url not in exclude
            and e.is_healthy
            and (now - e.last_used >= self._cooldown or e.total_uses == 0)
        ]

        if not available:
            # Reset fail counts if all exhausted
            if all(not e.is_healthy for e in self._entries):
                for e in self._entries:
                    e.fail_count = max(0, e.fail_count - 1)
                available = [
                    e for e in self._entries
                    if e.url not in exclude
                    and (now - e.last_used >= self._cooldown or e.total_uses == 0)
                ]

        # Sort: healthy first, then by latency, then by fail count
        available.sort(
            key=lambda e: (
                -e.health_score,  # Higher health first
                e.latency_factor,  # Lower latency first
                e.fail_count,  # Fewer fails first
            )
        )

        return available

    def next(self, exclude: Optional[set[str]] = None) -> Optional[str]:
        """Get next proxy (smart rotation)."""
        available = self._get_available(exclude)
        if not available:
            return None

        entry = available[0]
        entry.last_used = time.time()
        entry.total_uses += 1
        return entry.url

    def next_sticky(self, session_id: str, ttl: int = 300) -> Optional[str]:
        """Get sticky proxy for session (same proxy for entire flow)."""
        now = time.time()

        # Check existing sticky session
        if session_id in self._sticky_sessions:
            expiry = self._sticky_ttl.get(session_id, 0)
            if now < expiry:
                entry = self._sticky_sessions[session_id]
                entry.last_used = now
                entry.total_uses += 1
                return entry.url
            else:
                # Session expired, release proxy
                del self._sticky_sessions[session_id]
                del self._sticky_ttl[session_id]

        # Get new sticky proxy
        exclude = set(self._sticky_sessions.keys())
        available = self._get_available(exclude)
        if not available:
            return None

        entry = available[0]
        entry.last_used = now
        entry.total_uses += 1

        self._sticky_sessions[session_id] = entry
        self._sticky_ttl[session_id] = now + ttl

        log.info("Sticky session %s -> proxy %s (ttl=%ds)", session_id, entry.url[:30], ttl)
        return entry.url

    def release_sticky(self, session_id: str) -> None:
        """Release sticky session."""
        if session_id in self._sticky_sessions:
            del self._sticky_sessions[session_id]
            del self._sticky_ttl[session_id]

    def retry(self, failed_url: str, exclude: Optional[set[str]] = None) -> Optional[str]:
        """Get replacement proxy after failure."""
        self.mark_failed(failed_url)

        exclude = exclude or set()
        exclude.add(failed_url)

        return self.next(exclude=exclude)

    # ------------------------------------------------------------------ #
    # Health tracking
    # ------------------------------------------------------------------ #

    def mark_failed(self, proxy_url: str) -> None:
        """Mark proxy as failed."""
        for entry in self._entries:
            if entry.url == proxy_url:
                entry.fail_count += 1
                log.debug("Proxy marked failed: %s (count=%d)", proxy_url[:30], entry.fail_count)
                break

    def mark_success(self, proxy_url: str) -> None:
        """Mark proxy as successful."""
        for entry in self._entries:
            if entry.url == proxy_url:
                entry.success_count += 1
                if entry.fail_count > 0:
                    entry.fail_count = max(0, entry.fail_count - 1)
                break

    def detect_country(self, proxy_url: Optional[str] = None) -> ProxyInfo:
        """Detect country for a proxy."""
        return detect_proxy_country(proxy_url)

    @property
    def count(self) -> int:
        return len(self._entries)

    @property
    def available(self) -> int:
        return len(self._get_available())

    @property
    def healthy(self) -> int:
        return sum(1 for e in self._entries if e.is_healthy)

    def stats(self) -> dict:
        """Get proxy pool stats."""
        return {
            "total": self.count,
            "available": self.available,
            "healthy": self.healthy,
            "sticky_sessions": len(self._sticky_sessions),
        }
