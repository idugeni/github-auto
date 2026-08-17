"""Self-hosted CAPTCHA solver — HTTP-based, no browser."""

from __future__ import annotations

import logging
import re
from typing import Optional

from .base import CaptchaSolver

log = logging.getLogger(__name__)


class SelfHostedSolver(CaptchaSolver):
    """Unified self-hosted CAPTCHA solver via HTTP pattern matching."""

    def __init__(
        self,
        whisper_api_url: Optional[str] = None,
        whisper_api_key: Optional[str] = None,
        timeout: int = 180,
    ):
        self._timeout = timeout

    def solve(self, site_url: str, site_key: str, **kwargs) -> Optional[str]:
        """Extract CAPTCHA token from page HTML."""
        html = kwargs.get("html", "")
        captcha_type = self.detect_type(html)

        if captcha_type == "none":
            return None

        log.info("Detected CAPTCHA: %s", captcha_type)

        if captcha_type == "recaptcha":
            return self._extract_recaptcha(html)
        elif captcha_type == "turnstile":
            return self._extract_turnstile(html)
        elif captcha_type == "hcaptcha":
            return self._extract_hcaptcha(html)

        return None

    def detect_type(self, html: str) -> str:
        """Detect CAPTCHA type from HTML."""
        html_lower = html.lower()

        if "recaptcha" in html_lower or "grecaptcha" in html_lower:
            return "recaptcha"
        if "turnstile" in html_lower or "challenges.cloudflare.com" in html_lower:
            return "turnstile"
        if "hcaptcha" in html_lower or "hcaptcha.com" in html_lower:
            return "hcaptcha"

        return "none"

    def _extract_recaptcha(self, html: str) -> Optional[str]:
        """Extract reCAPTCHA token."""
        patterns = [
            r'name="g-recaptcha-response"[^>]*>([^<]+)',
            r'id="g-recaptcha-response"[^>]*>([^<]+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, html, re.I)
            if match:
                token = match.group(1).strip()
                if len(token) > 20:
                    return token
        return None

    def _extract_turnstile(self, html: str) -> Optional[str]:
        """Extract Turnstile token."""
        patterns = [
            r'name="cf-turnstile-response"[^>]*value="([^"]+)"',
            r'name="cf-turnstile-response"[^>]*>([^<]+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, html, re.I)
            if match:
                token = match.group(1).strip()
                if len(token) > 10:
                    return token
        return None

    def _extract_hcaptcha(self, html: str) -> Optional[str]:
        """Extract hCaptcha token."""
        patterns = [
            r'name="h-captcha-response"[^>]*value="([^"]+)"',
            r'<textarea[^>]*name="h-captcha-response"[^>]*>([^<]+)</textarea>',
        ]
        for pattern in patterns:
            match = re.search(pattern, html, re.I)
            if match:
                token = match.group(1).strip()
                if len(token) > 10:
                    return token
        return None
