"""Supabase temporary email provider (ported from autoregister-account)."""

from __future__ import annotations

import logging
import os
import re
import time
from typing import Optional

import requests

from .base import EmailProvider, Inbox

log = logging.getLogger(__name__)

DEFAULT_DOMAINS = ["openfile.my.id", "neorastorepl.my.id", "moymoy.me"]


class SupabaseInbox(Inbox):
    pass


class SupabaseEmailProvider(EmailProvider):
    """Supabase-backed temp email via Edge Functions + REST API."""

    def __init__(
        self,
        supabase_url: Optional[str] = None,
        anon_key: Optional[str] = None,
    ):
        self._url = supabase_url or os.getenv("SUPABASE_URL", "")
        self._key = anon_key or os.getenv("SUPABASE_ANON_KEY", "")
        if not self._url or not self._key:
            raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY required")

        self._session = requests.Session()
        self._session.headers.update({
            "apikey": self._key,
            "Authorization": f"Bearer {self._key}",
            "Content-Type": "application/json",
        })
        self._owner_token = os.urandom(16).hex()

    def _edge_function(self, name: str, data: dict) -> dict:
        url = f"{self._url}/functions/v1/{name}"
        resp = self._session.post(url, json=data)
        if resp.status_code != 200:
            raise RuntimeError(f"Edge function {name} failed: {resp.status_code} {resp.text}")
        return resp.json()

    def _rest_get(self, table: str, params: Optional[dict] = None) -> list:
        url = f"{self._url}/rest/v1/{table}"
        resp = self._session.get(url, params=params or {})
        if resp.status_code != 200:
            raise RuntimeError(f"REST GET {table} failed: {resp.status_code}")
        return resp.json()

    def create_inbox(
        self, username: str, domain: Optional[str] = None
    ) -> SupabaseInbox:
        if not domain:
            domains = self._get_active_domains()
            domain = next(
                (d for d in DEFAULT_DOMAINS if d in domains),
                domains[0] if domains else DEFAULT_DOMAINS[0],
            )

        data = self._edge_function("generate-inbox", {
            "owner_token": self._owner_token,
            "desired_local": username,
            "domain": domain,
        })

        address = data.get("address", f"{username}@{domain}")
        return SupabaseInbox(
            address=address,
            token=self._owner_token,
            domain=domain,
        )

    def _get_active_domains(self) -> list[str]:
        try:
            rows = self._rest_get("temp_domains", {
                "select": "domain",
                "is_active": "eq.true",
                "order": "priority.asc",
            })
            return [r["domain"] for r in rows]
        except Exception:
            return DEFAULT_DOMAINS

    def get_messages(self, address: str) -> list[dict]:
        return self._rest_get("temp_messages", {
            "inbox_address": f"eq.{address}",
            "order": "received_at.desc",
        })

    @staticmethod
    def _clean_html(raw: str) -> str:
        text = re.sub(r"<style[^>]*>.*?</style>", "", raw, flags=re.S)
        text = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.S)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"&nbsp;", " ", text)
        text = re.sub(r"&#\d+;", "", text)
        return text.strip()

    @staticmethod
    def _normalize_digits(text: str) -> str:
        return re.sub(r"[\s\-\.]+", "", text)

    @staticmethod
    def _is_year(code: str) -> bool:
        if len(code) == 4 and code.isdigit():
            return 1900 <= int(code) <= 2099
        return False

    @staticmethod
    def extract_otp(subject: str, text_body: str, html_body: str = "") -> Optional[str]:
        """Multi-pattern OTP extraction."""
        combined = f"{subject} {text_body} {SupabaseEmailProvider._clean_html(html_body)}"
        combined = SupabaseEmailProvider._normalize_digits(combined)

        # Pattern 1: keyword followed by digits
        kw_pattern = r"(?:otp|kode|code|verif|pin|password|token|verify)\D{0,40}?(\d{4,8})"
        match = re.search(kw_pattern, combined, re.I)
        if match and not SupabaseEmailProvider._is_year(match.group(1)):
            return match.group(1)

        # Pattern 2: digits followed by keyword
        kw_pattern2 = r"(\d{4,8})\D{0,20}?(?:otp|kode|code|verif|pin|password|token|verify)"
        match = re.search(kw_pattern2, combined, re.I)
        if match and not SupabaseEmailProvider._is_year(match.group(1)):
            return match.group(1)

        # Pattern 3: fallback any 4-8 digits
        for m in re.finditer(r"(\d{4,8})", combined):
            code = m.group(1)
            if not SupabaseEmailProvider._is_year(code):
                return code

        return None

    def poll_otp(
        self,
        address: str,
        sender_contains: Optional[str] = None,
        timeout: int = 120,
    ) -> str:
        """Poll for OTP. Raises TimeoutError on failure."""
        deadline = time.time() + timeout
        seen: set[str] = set()
        interval = 2.5

        while time.time() < deadline:
            try:
                messages = self.get_messages(address)
                for msg in messages:
                    msg_id = msg.get("id", "")
                    if msg_id in seen:
                        continue
                    seen.add(msg_id)

                    sender = msg.get("sender", "")
                    if sender_contains and sender_contains.lower() not in sender.lower():
                        continue

                    subject = msg.get("subject", "")
                    text_body = msg.get("text", msg.get("body", ""))
                    html_body = msg.get("html", "")
                    otp = self.extract_otp(subject, text_body, html_body)
                    if otp:
                        log.info("OTP extracted: %s...", otp[:3])
                        return otp
            except Exception as exc:
                log.debug("Poll error: %s", exc)

            elapsed = time.time() - (deadline - timeout)
            if elapsed > 90:
                interval = 10.0
            elif elapsed > 30:
                interval = 5.0

            time.sleep(min(interval, max(0.5, deadline - time.time())))

        raise TimeoutError(f"OTP timeout after {timeout}s for {address}")

    def delete_inbox(self, address: str, token: str = "") -> None:
        log.debug("Supabase inboxes are permanent, skip delete: %s", address)
