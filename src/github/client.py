"""Pure HTTP GitHub client — no browser required.

All operations via HTTP requests with:
- TLS fingerprint impersonation (curl_cffi)
- Cookie persistence
- Custom CAPTCHA solving
- Human-like request patterns
"""

from __future__ import annotations

import json
import logging
import os
import random
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from curl_cffi.requests import Session

log = logging.getLogger(__name__)

GITHUB_HOME = "https://github.com/"
GITHUB_SIGNUP = "https://github.com/signup"
GITHUB_SESSION = "https://github.com/session"
GITHUB_VERIFY = "https://github.com/account_verifications"

COOKIES_FILE = "data/github_cookies.json"

# Request headers to mimic real browser
DEFAULT_HEADERS = {
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
}


@dataclass
class ClientResult:
    success: bool = False
    data: dict = field(default_factory=dict)
    error: str = ""
    cookies: dict = field(default_factory=dict)


class GithubClient:
    """Pure HTTP GitHub client.

    Uses curl_cffi for TLS fingerprint impersonation.
    No browser required.
    """

    def __init__(
        self,
        proxy: Optional[str] = None,
        impersonate: str = "chrome131",
        cookies_file: str = COOKIES_FILE,
    ):
        self._proxy = proxy
        self._impersonate = impersonate
        self._cookies_file = Path(cookies_file)
        self._session: Optional[Session] = None
        self._cookies: dict = {}
        self._csrf_token: str = ""

    def _get_session(self) -> Session:
        """Get or create curl_cffi session."""
        if self._session is None:
            self._session = Session(impersonate=self._impersonate)  # type: ignore
            if self._proxy:
                self._session.proxies = {
                    "http": self._proxy,
                    "https": self._proxy,
                }
            self._session.headers.update(DEFAULT_HEADERS)

            # Load saved cookies
            self._load_cookies()

        return self._session

    def _human_delay(self, min_ms: int = 200, max_ms: int = 800) -> None:
        """Human-like delay between requests."""
        time.sleep(random.uniform(min_ms / 1000, max_ms / 1000))

    def _extract_csrf_token(self, html: str) -> str:
        """Extract CSRF token from HTML."""
        patterns = [
            r'<meta name="csrf-token" content="([^"]+)"',
            r'name="authenticity_token" value="([^"]+)"',
            r'value="([^"]+)"\s+name="authenticity_token"',
        ]
        for pattern in patterns:
            match = re.search(pattern, html)
            if match:
                return match.group(1)
        return ""

    def _extract_hidden_fields(self, html: str) -> dict:
        """Extract hidden form fields."""
        fields = {}
        for match in re.finditer(
            r'<input[^>]*type="hidden"[^>]*name="([^"]+)"[^>]*value="([^"]*)"',
            html,
        ):
            fields[match.group(1)] = match.group(2)
        # Try reversed attribute order
        for match in re.finditer(
            r'<input[^>]*name="([^"]+)"[^>]*type="hidden"[^>]*value="([^"]*)"',
            html,
        ):
            fields[match.group(1)] = match.group(2)
        return fields

    def _load_cookies(self) -> None:
        """Load cookies from file."""
        if self._cookies_file.exists():
            try:
                data = json.loads(self._cookies_file.read_text(encoding="utf-8"))
                if data and self._session:
                    self._session.cookies.update(data)
                    self._cookies = data
                    log.debug("Loaded %d cookies", len(data))
            except Exception as exc:
                log.debug("Failed to load cookies: %s", exc)

    def _save_cookies(self) -> None:
        """Save cookies to file."""
        if self._session:
            self._cookies = dict(self._session.cookies)
            self._cookies_file.parent.mkdir(parents=True, exist_ok=True)
            self._cookies_file.write_text(
                json.dumps(self._cookies, indent=2),
                encoding="utf-8",
            )

    # ------------------------------------------------------------------ #
    # Core HTTP methods
    # ------------------------------------------------------------------ #

    def get(self, url: str, **kwargs) -> dict:
        """Make GET request."""
        session = self._get_session()
        kwargs.setdefault("timeout", 20)
        kwargs.setdefault("allow_redirects", True)

        resp = session.get(url, **kwargs)
        self._save_cookies()

        return {
            "status": resp.status_code,
            "url": resp.url,
            "text": resp.text,
            "headers": dict(resp.headers),
        }

    def post(self, url: str, data: Optional[dict] = None, **kwargs) -> dict:
        """Make POST request."""
        session = self._get_session()
        kwargs.setdefault("timeout", 20)
        kwargs.setdefault("allow_redirects", True)

        resp = session.post(url, data=data, **kwargs)
        self._save_cookies()

        return {
            "status": resp.status_code,
            "url": resp.url,
            "text": resp.text,
            "headers": dict(resp.headers),
        }

    # ------------------------------------------------------------------ #
    # GitHub operations
    # ------------------------------------------------------------------ #

    def warmup(self) -> bool:
        """Warmup session by visiting homepage."""
        log.info("Warming up session...")
        result = self.get(GITHUB_HOME)
        self._human_delay(1000, 2000)
        return result["status"] == 200

    def get_signup_page(self) -> ClientResult:
        """Get signup page and extract tokens."""
        result = self.get(GITHUB_SIGNUP)

        if result["status"] != 200:
            return ClientResult(
                success=False,
                error=f"Signup page returned {result['status']}",
            )

        html = result["text"]
        csrf = self._extract_csrf_token(html)
        fields = self._extract_hidden_fields(html)

        self._csrf_token = csrf

        return ClientResult(
            success=True,
            data={
                "csrf_token": csrf,
                "fields": fields,
                "has_form": "email" in html.lower() or "#email" in html,
            },
        )

    def submit_signup(
        self,
        email: str,
        password: str,
        username: str,
    ) -> ClientResult:
        """Submit signup form."""
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
            "Referer": GITHUB_SIGNUP,
        }

        result = self.post(GITHUB_SIGNUP, data=data, headers=headers)

        location = result["headers"].get("location", "")
        is_verification = "account_verifications" in location
        is_blocked = "access is temporarily restricted" in result["text"].lower()

        return ClientResult(
            success=is_verification,
            data={
                "status": result["status"],
                "location": location,
                "is_verification": is_verification,
                "is_blocked": is_blocked,
            },
            error="Blocked" if is_blocked else ("Not verification" if not is_verification else ""),
        )

    def check_verification(self) -> ClientResult:
        """Check verification page."""
        result = self.get(GITHUB_VERIFY)

        html = result["text"]
        has_otp = bool(re.search(r'maxlength="6"', html))
        has_challenge = any(
            marker in html.lower()
            for marker in ["unusual activity", "verification", "octocaptcha"]
        )

        return ClientResult(
            success=result["status"] == 200,
            data={
                "has_otp_input": has_otp,
                "has_challenge": has_challenge,
                "is_verification": has_otp,
            },
        )

    def submit_otp(self, code: str) -> ClientResult:
        """Submit OTP verification code."""
        data = {
            "authenticity_token": self._csrf_token,
            "otp": code,
            "commit": "Verify",
        }

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": "https://github.com",
            "Referer": GITHUB_VERIFY,
        }

        result = self.post(GITHUB_VERIFY, data=data, headers=headers)

        location = result["headers"].get("location", "")
        success = result["status"] == 302 and "dashboard" in location

        return ClientResult(
            success=success,
            data={
                "status": result["status"],
                "location": location,
            },
            error="" if success else "OTP verification failed",
        )

    def get_cookies(self) -> dict:
        """Get current session cookies."""
        return self._cookies.copy()

    def close(self) -> None:
        """Close session."""
        self._save_cookies()
        if self._session:
            self._session.close()
            self._session = None
