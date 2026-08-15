"""Gmail OAuth2 temp email provider."""

from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path
from typing import Optional

import requests

from .base import EmailProvider, Inbox

log = logging.getLogger(__name__)

GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_REVOKE_URL = "https://oauth2.googleapis.com/revoke"
GMAIL_API_URL = "https://www.googleapis.com/gmail/v1/users/me/messages"


class GmailInbox(Inbox):
    pass


class GmailProvider(EmailProvider):
    """Gmail OAuth2 provider for temporary emails.

    Uses Gmail API to read verification emails.
    Requires OAuth2 credentials and refresh token.
    """

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        refresh_token: Optional[str] = None,
        tokens_file: str = "data/gmail_tokens.json",
    ):
        self._client_id = client_id or os.getenv("GMAIL_CLIENT_ID", "")
        self._client_secret = client_secret or os.getenv("GMAIL_CLIENT_SECRET", "")
        self._refresh_token = refresh_token or os.getenv("GMAIL_REFRESH_TOKEN", "")
        self._tokens_file = Path(tokens_file)
        self._access_token = ""
        self._token_expiry = 0.0

        # Load tokens from file if exists
        self._load_tokens()

    def _load_tokens(self) -> None:
        """Load tokens from file."""
        if self._tokens_file.exists():
            try:
                data = json.loads(self._tokens_file.read_text(encoding="utf-8"))
                self._refresh_token = data.get("refresh_token", self._refresh_token)
                self._access_token = data.get("access_token", "")
                self._token_expiry = data.get("expiry", 0.0)
            except Exception as exc:
                log.debug("Failed to load tokens: %s", exc)

    def _save_tokens(self) -> None:
        """Save tokens to file."""
        self._tokens_file.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "refresh_token": self._refresh_token,
            "access_token": self._access_token,
            "expiry": self._token_expiry,
        }
        self._tokens_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def _refresh_access_token(self) -> str:
        """Refresh access token using refresh token."""
        if not self._client_id or not self._client_secret or not self._refresh_token:
            raise RuntimeError("Gmail OAuth credentials not configured")

        resp = requests.post(GOOGLE_TOKEN_URL, data={
            "client_id": self._client_id,
            "client_secret": self._client_secret,
            "refresh_token": self._refresh_token,
            "grant_type": "refresh_token",
        })

        if resp.status_code != 200:
            raise RuntimeError(f"Token refresh failed: {resp.status_code} {resp.text}")

        data = resp.json()
        self._access_token = data["access_token"]
        self._token_expiry = time.time() + data.get("expires_in", 3600)
        self._save_tokens()
        return self._access_token

    def _get_access_token(self) -> str:
        """Get valid access token, refreshing if needed."""
        if time.time() >= self._token_expiry - 60:
            return self._refresh_access_token()
        return self._access_token

    def _gmail_request(self, endpoint: str, params: Optional[dict] = None) -> dict:
        """Make authenticated Gmail API request."""
        token = self._get_access_token()
        headers = {"Authorization": f"Bearer {token}"}
        resp = requests.get(f"{GMAIL_API_URL}/{endpoint}", headers=headers, params=params)

        if resp.status_code == 401:
            # Token expired, refresh and retry
            token = self._refresh_access_token()
            headers = {"Authorization": f"Bearer {token}"}
            resp = requests.get(f"{GMAIL_API_URL}/{endpoint}", headers=headers, params=params)

        if resp.status_code != 200:
            raise RuntimeError(f"Gmail API error: {resp.status_code} {resp.text}")

        return resp.json()

    def create_inbox(self, username: str, domain: Optional[str] = None) -> GmailInbox:
        """Create inbox (Gmail uses existing account).

        For Gmail, username is the email prefix.
        Domain is ignored (always @gmail.com).
        """
        address = f"{username}@gmail.com"
        return GmailInbox(
            address=address,
            token=self._refresh_token,
            domain="gmail.com",
        )

    def get_messages(self, address: str, query: str = "") -> list[dict]:
        """Fetch messages from Gmail."""
        search_query = query or f"to:{address}"
        result = self._gmail_request("", params={"q": search_query, "maxResults": 10})
        messages = result.get("messages", [])

        detailed = []
        for msg in messages:
            try:
                detail = self._gmail_request(msg["id"])
                detailed.append(detail)
            except Exception as exc:
                log.debug("Failed to fetch message %s: %s", msg["id"], exc)

        return detailed

    def _extract_body(self, message: dict) -> str:
        """Extract text body from Gmail message."""
        payload = message.get("payload", {})
        parts = payload.get("parts", [])

        if not parts:
            # Single part message
            body = payload.get("body", {})
            data = body.get("data", "")
            if data:
                import base64
                return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
            return ""

        # Multipart message
        for part in parts:
            if part.get("mimeType") == "text/plain":
                body = part.get("body", {})
                data = body.get("data", "")
                if data:
                    import base64
                    return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")

        return ""

    def _extract_subject(self, message: dict) -> str:
        """Extract subject from Gmail message."""
        headers = message.get("payload", {}).get("headers", [])
        for header in headers:
            if header.get("name", "").lower() == "subject":
                return header.get("value", "")
        return ""

    def _extract_sender(self, message: dict) -> str:
        """Extract sender from Gmail message."""
        headers = message.get("payload", {}).get("headers", [])
        for header in headers:
            if header.get("name", "").lower() == "from":
                return header.get("value", "")
        return ""

    def poll_otp(
        self,
        address: str,
        sender_contains: Optional[str] = None,
        timeout: int = 120,
    ) -> str:
        """Poll for OTP code from Gmail."""
        from src.email.supabase import SupabaseEmailProvider

        deadline = time.time() + timeout
        seen: set[str] = set()

        while time.time() < deadline:
            try:
                messages = self.get_messages(address)
                for msg in messages:
                    msg_id = msg.get("id", "")
                    if msg_id in seen:
                        continue
                    seen.add(msg_id)

                    sender = self._extract_sender(msg)
                    if sender_contains and sender_contains.lower() not in sender.lower():
                        continue

                    subject = self._extract_subject(msg)
                    body = self._extract_body(msg)
                    otp = SupabaseEmailProvider.extract_otp(subject, body)
                    if otp:
                        log.info("OTP extracted from Gmail: %s...", otp[:3])
                        return otp
            except Exception as exc:
                log.debug("Gmail poll error: %s", exc)

            time.sleep(3)

        raise TimeoutError(f"Gmail OTP timeout after {timeout}s for {address}")

    def delete_inbox(self, address: str, token: str = "") -> None:
        """Gmail inboxes are permanent, skip delete."""
        log.debug("Gmail inbox is permanent, skip delete: %s", address)
