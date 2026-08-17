"""reCAPTCHA solver — HTTP-based pattern extraction."""

from __future__ import annotations

import logging
import os
import re
from typing import Optional

from .base import CaptchaSolver

log = logging.getLogger(__name__)


class RecaptchaAudioSolver(CaptchaSolver):
    """Extract reCAPTCHA token from HTML via pattern matching."""

    def __init__(self, groq_api_key: Optional[str] = None, max_attempts: int = 3):
        self._api_key = groq_api_key or os.getenv("GROQ_API_KEY", "")

    def solve(self, site_url: str, site_key: str, **kwargs) -> Optional[str]:
        """Extract reCAPTCHA response token from page HTML."""
        html = kwargs.get("html", "")
        return self._extract_token(html)

    def _extract_token(self, html: str) -> Optional[str]:
        """Extract g-recaptcha-response from HTML."""
        patterns = [
            r'name="g-recaptcha-response"[^>]*>([^<]+)',
            r'id="g-recaptcha-response"[^>]*>([^<]+)',
            r"g-recaptcha-response['\"]\s*:\s*['\"]([^'\"]+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, html, re.I)
            if match:
                token = match.group(1).strip()
                if len(token) > 20:
                    log.info("reCAPTCHA token extracted (%d chars)", len(token))
                    return token
        return None
