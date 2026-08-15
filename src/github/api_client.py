"""GitHub API client for browserless operations.

Uses curl_cffi for TLS fingerprint impersonation to avoid bot detection.
Replaces browser automation where possible for speed and stealth.

Flow:
1. Warmup session (visit homepage)
2. Get signup page tokens
3. Submit registration form
4. Handle verification (OTP from email)
5. Complete account setup
"""

from __future__ import annotations

import logging
import random
import re
import time
from dataclasses import dataclass, field
from typing import Optional

from curl_cffi.requests import Session

log = logging.getLogger(__name__)


@dataclass
class SignupResult:
    success: bool = False
    username: str = ""
    password: str = ""
    email: str = ""
    error: str = ""
    duration_sec: float = 0.0
    cookies: dict = field(default_factory=dict)


class GithubApiClient:
    """Browserless GitHub client using curl_cffi.

    Uses Chrome TLS impersonation to bypass bot detection.
    Much faster than browser automation.
    """

    def __init__(
        self,
        proxy: Optional[str] = None,
        impersonate: str = "chrome131",
    ):
        self._proxy = proxy
        self._impersonate = impersonate
        self._session: Optional[Session] = None
        self._csrf_token: str = ""
        self._cookies: dict = {}

    def _get_session(self) -> Session:
        """Get or create curl_cffi session."""
        if self._session is None:
            self._session = Session(impersonate=self._impersonate)  # type: ignore
            if self._proxy:
                self._session.proxies = {
                    "http": self._proxy,
                    "https": self._proxy,
                }
            # Set realistic headers
            self._session.headers.update({
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate, br",
                "DNT": "1",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
            })
        return self._session

    def _human_delay(self, min_ms: int = 100, max_ms: int = 500) -> None:
        """Simulate human-like delay between requests."""
        time.sleep(random.uniform(min_ms / 1000, max_ms / 1000))

    def _extract_csrf_token(self, html: str) -> str:
        """Extract CSRF token from HTML."""
        # Meta tag
        match = re.search(r'<meta name="csrf-token" content="([^"]+)"', html)
        if match:
            return match.group(1)

        # Hidden input
        match = re.search(r'name="authenticity_token" value="([^"]+)"', html)
        if match:
            return match.group(1)

        return ""

    def _extract_form_fields(self, html: str) -> dict:
        """Extract hidden form fields."""
        fields = {}
        for match in re.finditer(
            r'<input[^>]*type="hidden"[^>]*name="([^"]+)"[^>]*value="([^"]*)"',
            html,
        ):
            fields[match.group(1)] = match.group(2)

        # Also try reversed attribute order
        for match in re.finditer(
            r'<input[^>]*name="([^"]+)"[^>]*type="hidden"[^>]*value="([^"]*)"',
            html,
        ):
            fields[match.group(1)] = match.group(2)

        return fields

    def warmup(self) -> bool:
        """Warmup session by visiting homepage."""
        session = self._get_session()
        try:
            resp = session.get("https://github.com/", timeout=20)
            self._cookies.update(dict(session.cookies))
            log.info("Warmup: %d", resp.status_code)
            return resp.status_code == 200
        except Exception as exc:
            log.warning("Warmup failed: %s", exc)
            return False

    def get_signup_page(self) -> dict:
        """Get signup page and extract tokens."""
        session = self._get_session()
        resp = session.get("https://github.com/signup", timeout=20)
        html = resp.text

        csrf = self._extract_csrf_token(html)
        fields = self._extract_form_fields(html)

        self._csrf_token = csrf

        return {
            "csrf_token": csrf,
            "fields": fields,
            "status_code": resp.status_code,
        }

    def submit_signup(
        self,
        email: str,
        password: str,
        username: str,
    ) -> dict:
        """Submit signup form."""
        session = self._get_session()

        data = {
            "authenticity_token": self._csrf_token,
            "email": email,
            "password": password,
            "login": username,
            "user_signup_copilot_opt_in": "0",
            "user_signup_marketing_consent": "0",
            "commit": "Create account",
        }

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": "https://github.com",
            "Referer": "https://github.com/signup",
        }

        resp = session.post(
            "https://github.com/signup",
            data=data,
            headers=headers,
            timeout=20,
        )

        self._cookies.update(dict(session.cookies))

        return {
            "status_code": resp.status_code,
            "location": resp.headers.get("location", ""),
            "is_verification": "account_verifications" in resp.headers.get("location", ""),
            "is_blocked": "access is temporarily restricted" in resp.text.lower(),
        }

    def check_verification_page(self) -> dict:
        """Check if we're on verification page."""
        session = self._get_session()
        resp = session.get("https://github.com/account_verifications", timeout=20)
        html = resp.text

        # Check for OTP input
        has_otp_input = bool(re.search(r'maxlength="6"', html))

        # Check for challenge markers
        challenge_markers = [
            "unusual activity",
            "verification",
            "octocaptcha",
            "confirm your account",
        ]
        has_challenge = any(marker in html.lower() for marker in challenge_markers)

        return {
            "status_code": resp.status_code,
            "has_otp_input": has_otp_input,
            "has_challenge": has_challenge,
            "is_verification": resp.status_code == 200 and has_otp_input,
        }

    def submit_otp(self, code: str) -> dict:
        """Submit OTP verification code."""
        session = self._get_session()

        data = {
            "authenticity_token": self._csrf_token,
            "otp": code,
            "commit": "Verify",
        }

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": "https://github.com",
            "Referer": "https://github.com/account_verifications",
        }

        resp = session.post(
            "https://github.com/account_verifications",
            data=data,
            headers=headers,
            timeout=20,
        )

        self._cookies.update(dict(session.cookies))

        return {
            "status_code": resp.status_code,
            "location": resp.headers.get("location", ""),
            "success": resp.status_code == 302 and "dashboard" in resp.headers.get("location", ""),
        }

    def get_session_cookies(self) -> dict:
        """Get current session cookies."""
        return self._cookies.copy()

    def close(self) -> None:
        """Close session."""
        if self._session:
            self._session.close()
            self._session = None
