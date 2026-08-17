"""Cloudflare Turnstile solver — HTTP-based pattern extraction."""

from __future__ import annotations

import logging
import re
from typing import Optional

from .base import CaptchaSolver

log = logging.getLogger(__name__)


class TurnstileSolver(CaptchaSolver):
    """Extract Turnstile token from HTML via pattern matching."""

    def __init__(self, timeout: int = 180):
        self._timeout = timeout

    def solve(self, site_url: str, site_key: str, **kwargs) -> Optional[str]:
        """Extract Turnstile response token from page HTML."""
        html = kwargs.get("html", "")
        return self._extract_token(html)

    def _extract_token(self, html: str) -> Optional[str]:
        """Extract cf-turnstile-response from HTML."""
        patterns = [
            r'name="cf-turnstile-response"[^>]*value="([^"]+)"',
            r'name="cf-turnstile-response"[^>]*>([^<]+)',
            r"turnstile\.getResponse\(\)\s*\|\|\s*['\"]([^'\"]+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, html, re.I)
            if match:
                token = match.group(1).strip()
                if len(token) > 10:
                    log.info("Turnstile token extracted (%d chars)", len(token))
                    return token
        return None
