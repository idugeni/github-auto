"""GitHub Octocaptcha solver — HTTP-based detection."""

from __future__ import annotations

import logging
import re
from typing import Optional

from .base import CaptchaSolver

log = logging.getLogger(__name__)

CHALLENGE_MARKERS = (
    "unusual activity",
    "verification",
    "octocaptcha",
    "confirm your account",
    "checkpoint",
    "verify your identity",
    "we sent you",
    "check your email",
    "device verification",
    "two-factor",
    "2fa",
)


class OctocaptchaSolver(CaptchaSolver):
    """Detect and extract GitHub challenge tokens from HTML."""

    def __init__(self, timeout: int = 180):
        self._timeout = timeout

    def solve(self, site_url: str, site_key: str, **kwargs) -> Optional[str]:
        """Detect GitHub challenge and extract verification token."""
        html = kwargs.get("html", "")
        return self._extract_verification_token(html)

    def detect_challenge(self, html: str) -> str:
        """Detect challenge type from HTML."""
        html_lower = html.lower()

        if "device verification" in html_lower or "verify your identity" in html_lower:
            return "device_verification"
        if "two-factor" in html_lower or "2fa" in html_lower:
            return "two_factor"
        if "unusual activity" in html_lower or "checkpoint" in html_lower:
            return "unusual_activity"
        if self._has_code_input(html):
            return "code_input"
        if "passkey" in html_lower or "security key" in html_lower:
            return "passkey_required"

        return "none"

    def _has_code_input(self, html: str) -> bool:
        """Check for OTP/code input fields in HTML."""
        patterns = [
            r'name="otp"',
            r'name="code"',
            r'name="verification_code"',
            r'maxlength="6"',
            r'maxlength="8"',
        ]
        return any(re.search(p, html, re.I) for p in patterns)

    def _extract_verification_token(self, html: str) -> Optional[str]:
        """Extract verification token from HTML."""
        patterns = [
            r'name="authenticity_token"[^>]*value="([^"]+)"',
            r'name="authenticity_token"[^>]*>([^<]+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, html, re.I)
            if match:
                token = match.group(1).strip()
                if len(token) > 10:
                    log.info("Verification token extracted (%d chars)", len(token))
                    return token
        return None

    def extract_code_from_text(self, text: str) -> Optional[str]:
        """Extract 6-digit verification code from text."""
        match = re.search(r"code\s*(?:is|:)\s*(\d{6})", text, re.I)
        if match:
            return match.group(1)
        match = re.search(r"\b(\d{6})\b", text)
        if match:
            return match.group(1)
        return None
