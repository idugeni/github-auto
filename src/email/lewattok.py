"""LewatTok temporary email provider."""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass
from typing import Optional

import requests

from .base import EmailProvider, Inbox

log = logging.getLogger(__name__)

BASE_URL = os.getenv("LEWATTOK_BASE_URL", "https://api.lewattok.web.id")
DEFAULT_DOMAINS = [
    "lewattok.web.id", "neorastorepl.my.id", "openfile.my.id",
    "moymoy.me", "mail.wubook.net", "inbox.tmpmail.net",
]


@dataclass
class LewatTokInbox(Inbox):
    inbox_token: str = ""
    permanent: bool = True


class LewatTokClient(EmailProvider):
    """LewatTok API client for temporary emails."""

    def __init__(self, api_key: Optional[str] = None):
        self._api_key = api_key or os.getenv("LEWATTOK_API_KEY", "")
        self._session = requests.Session()
        if self._api_key:
            self._session.headers["X-API-Key"] = self._api_key

    def _poll_interval(self) -> float:
        return 1.5 if self._api_key else 4.0

    def create_inbox(
        self, username: str, domain: Optional[str] = None
    ) -> LewatTokInbox:
        """Create a new inbox. domain defaults to first available."""
        if not domain:
            domain = DEFAULT_DOMAINS[0]

        resp = self._session.post(
            f"{BASE_URL}/v1/inboxes",
            json={"username": username, "domain": domain},
        )
        if resp.status_code == 409:
            raise RuntimeError(f"INBOX_EXISTS: {username}@{domain}")
        if resp.status_code != 201:
            raise RuntimeError(
                f"Inbox creation failed: {resp.status_code} {resp.text}"
            )

        data = resp.json()
        return LewatTokInbox(
            address=data.get("address", f"{username}@{domain}"),
            inbox_token=data.get("inbox_token", ""),
            domain=domain,
        )

    def get_messages(
        self,
        address: str,
        since: Optional[str] = None,
        limit: int = 50,
    ) -> tuple[list[dict], str]:
        """Fetch messages for an inbox."""
        params: dict = {"recipient": address, "limit": limit}
        if since:
            params["since"] = since

        resp = self._session.get(f"{BASE_URL}/v1/messages", params=params)
        if resp.status_code == 304:
            return [], since or ""
        if resp.status_code != 200:
            raise RuntimeError(
                f"Get messages failed: {resp.status_code} {resp.text}"
            )

        data = resp.json()
        messages = data if isinstance(data, list) else data.get("messages", [])
        latest = since or ""
        for msg in messages:
            created = msg.get("created_at", "")
            if created > latest:
                latest = created
        return messages, latest

    def _filter_otp(
        self,
        messages: list[dict],
        sender_contains: Optional[str] = None,
    ) -> list[dict]:
        """Filter messages that have an OTP code."""
        result = []
        for msg in messages:
            if "otp_code" not in msg:
                continue
            if sender_contains:
                sender = msg.get("sender", "").lower()
                if sender_contains.lower() not in sender:
                    continue
            result.append(msg)
        return result

    def poll_otp(
        self,
        address: str,
        sender_contains: Optional[str] = None,
        timeout: int = 120,
    ) -> str:
        """Poll for OTP code. Raises TimeoutError on failure."""
        deadline = time.time() + timeout
        since: Optional[str] = None
        interval = self._poll_interval()

        while time.time() < deadline:
            messages, since = self.get_messages(address, since=since)
            otp_msgs = self._filter_otp(messages, sender_contains)
            if otp_msgs:
                code = otp_msgs[0].get("otp_code", "")
                if code:
                    log.info("OTP received: %s... (length=%d)", code[:3], len(code))
                    return code

            remaining = deadline - time.time()
            sleep_time = min(interval, max(0.5, remaining))
            time.sleep(sleep_time)

        raise TimeoutError(f"OTP timeout after {timeout}s for {address}")

    def delete_inbox(self, address: str, token: str = "") -> None:
        """Delete an inbox."""
        headers = {}
        if token:
            headers["X-Inbox-Token"] = token
        resp = self._session.delete(
            f"{BASE_URL}/v1/inboxes/{address}",
            headers=headers,
        )
        if resp.status_code == 404:
            log.debug("Inbox already deleted: %s", address)
        elif resp.status_code != 200:
            log.warning("Delete inbox failed: %s %s", resp.status_code, resp.text)
        else:
            log.debug("Inbox deleted: %s", address)

    def get_domains(self) -> list[dict]:
        """List available domains."""
        resp = self._session.get(f"{BASE_URL}/v1/domains")
        if resp.status_code != 200:
            raise RuntimeError(f"Get domains failed: {resp.status_code}")
        return resp.json()
