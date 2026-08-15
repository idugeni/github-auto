"""Mail.tm temporary email provider."""

from __future__ import annotations

import logging
import os
import re
import time
from typing import Optional

import requests

from .base import EmailProvider, Inbox

log = logging.getLogger(__name__)

MAILTM_API_URL = "https://api.mail.tm"


class MailTmInbox(Inbox):
    pass


class MailTmProvider(EmailProvider):
    """Mail.tm temporary email provider.

    Free temp email service with API access.
    """

    def __init__(self, api_token: Optional[str] = None):
        self._token = api_token or os.getenv("MAILTM_API_TOKEN", "")
        self._session = requests.Session()
        if self._token:
            self._session.headers["Authorization"] = f"Bearer {self._token}"

    def _get_domains(self) -> list[dict]:
        """Get available domains."""
        resp = self._session.get(f"{MAILTM_API_URL}/domains")
        if resp.status_code != 200:
            raise RuntimeError(f"Failed to get domains: {resp.status_code}")
        return resp.json().get("hydra:member", [])

    def _create_account(self, address: str, password: str) -> dict:
        """Create a mail.tm account."""
        resp = self._session.post(f"{MAILTM_API_URL}/accounts", json={
            "address": address,
            "password": password,
        })
        if resp.status_code == 201:
            return resp.json()
        elif resp.status_code == 422:
            raise RuntimeError(f"Account already exists: {address}")
        else:
            raise RuntimeError(f"Failed to create account: {resp.status_code} {resp.text}")

    def _get_token(self, address: str, password: str) -> str:
        """Get authentication token."""
        resp = self._session.post(f"{MAILTM_API_URL}/token", json={
            "address": address,
            "password": password,
        })
        if resp.status_code != 200:
            raise RuntimeError(f"Failed to get token: {resp.status_code}")
        return resp.json().get("token", "")

    def _get_messages(self) -> list[dict]:
        """Get messages for authenticated account."""
        resp = self._session.get(f"{MAILTM_API_URL}/messages")
        if resp.status_code != 200:
            raise RuntimeError(f"Failed to get messages: {resp.status_code}")
        return resp.json().get("hydra:member", [])

    def _get_message(self, message_id: str) -> dict:
        """Get single message details."""
        resp = self._session.get(f"{MAILTM_API_URL}/messages/{message_id}")
        if resp.status_code != 200:
            raise RuntimeError(f"Failed to get message: {resp.status_code}")
        return resp.json()

    def create_inbox(self, username: str, domain: Optional[str] = None) -> MailTmInbox:
        """Create a new temp email inbox."""
        domains = self._get_domains()
        if not domains:
            raise RuntimeError("No available domains")

        if domain:
            # Find specific domain
            domain_info = next((d for d in domains if d["domain"] == domain), None)
            if not domain_info:
                raise RuntimeError(f"Domain not found: {domain}")
        else:
            domain_info = domains[0]

        email = f"{username}@{domain_info['domain']}"
        password = f"Pass{username}123!"

        try:
            account = self._create_account(email, password)
            token = self._get_token(email, password)
            self._session.headers["Authorization"] = f"Bearer {token}"

            return MailTmInbox(
                address=email,
                token=token,
                domain=domain_info["domain"],
            )
        except RuntimeError as exc:
            if "already exists" in str(exc):
                # Try to login to existing account
                try:
                    token = self._get_token(email, password)
                    self._session.headers["Authorization"] = f"Bearer {token}"
                    return MailTmInbox(
                        address=email,
                        token=token,
                        domain=domain_info["domain"],
                    )
                except Exception:
                    raise RuntimeError(f"Failed to create or login to inbox: {exc}")
            raise

    def poll_otp(
        self,
        address: str,
        sender_contains: Optional[str] = None,
        timeout: int = 120,
    ) -> str:
        """Poll for OTP code."""
        from src.email.supabase import SupabaseEmailProvider

        deadline = time.time() + timeout
        seen: set[str] = set()

        while time.time() < deadline:
            try:
                messages = self._get_messages()
                for msg in messages:
                    msg_id = msg.get("id", "")
                    if msg_id in seen:
                        continue
                    seen.add(msg_id)

                    sender = msg.get("from", {}).get("address", "")
                    if sender_contains and sender_contains.lower() not in sender.lower():
                        continue

                    # Get full message
                    detail = self._get_message(msg_id)
                    subject = detail.get("subject", "")
                    intro = detail.get("intro", "")

                    otp = SupabaseEmailProvider.extract_otp(subject, intro)
                    if otp:
                        log.info("OTP extracted from Mail.tm: %s...", otp[:3])
                        return otp
            except Exception as exc:
                log.debug("Mail.tm poll error: %s", exc)

            time.sleep(3)

        raise TimeoutError(f"Mail.tm OTP timeout after {timeout}s for {address}")

    def delete_inbox(self, address: str, token: str = "") -> None:
        """Delete mail.tm account."""
        try:
            # Get account ID
            resp = self._session.get(f"{MAILTM_API_URL}/accounts/me")
            if resp.status_code == 200:
                account_id = resp.json().get("id", "")
                if account_id:
                    self._session.delete(f"{MAILTM_API_URL}/accounts/{account_id}")
                    log.debug("Mail.tm account deleted: %s", address)
        except Exception as exc:
            log.debug("Failed to delete Mail.tm account: %s", exc)
