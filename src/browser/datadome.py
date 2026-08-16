"""DataDome bypass module.

Handles DataDome CAPTCHA challenges on GitHub.
Strategy:
1. Collect DataDome cookies from homepage
2. Solve CAPTCHA if challenged
3. Persist cookies for session reuse
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path

from playwright.sync_api import Page

log = logging.getLogger(__name__)

DATADOME_DOMAINS = [
    "captcha-delivery.com",
    "datadome.co",
]

DATADOME_COOKIES_FILE = "data/datadome_cookies.json"


class DataDomeBypass:
    """Bypass DataDome anti-bot protection."""

    def __init__(self, cookies_file: str = DATADOME_COOKIES_FILE):
        self._cookies_file = Path(cookies_file)
        self._cookies: dict = {}

    def load_cookies(self, context) -> bool:
        """Load saved DataDome cookies into browser context."""
        if not self._cookies_file.exists():
            return False

        try:
            data = json.loads(self._cookies_file.read_text(encoding="utf-8"))
            if data:
                context.add_cookies(data)
                log.info("Loaded %d DataDome cookies", len(data))
                return True
        except Exception as exc:
            log.debug("Failed to load DataDome cookies: %s", exc)

        return False

    def save_cookies(self, context) -> None:
        """Save DataDome cookies from browser context."""
        try:
            cookies = context.cookies()
            datadome_cookies = [
                c for c in cookies
                if any(d in c.get("domain", "") for d in DATADOME_DOMAINS)
            ]

            if datadome_cookies:
                self._cookies_file.parent.mkdir(parents=True, exist_ok=True)
                self._cookies_file.write_text(
                    json.dumps(datadome_cookies, indent=2),
                    encoding="utf-8",
                )
                log.info("Saved %d DataDome cookies", len(datadome_cookies))
        except Exception as exc:
            log.debug("Failed to save DataDome cookies: %s", exc)

    def is_challenge(self, page: Page) -> bool:
        """Check if page shows DataDome challenge."""
        try:
            url = page.url
            # Check URL
            if "captcha-delivery.com" in url or "datadome" in url:
                return True

            # Check for DataDome iframe
            iframe_count = page.locator("iframe[src*='captcha-delivery']").count()
            if iframe_count > 0:
                return True

            # Check for DataDome elements
            body = page.inner_text("body")[:500].lower()
            if "datadome" in body or "captcha" in body or "access denied" in body:
                return True

        except Exception:
            pass

        return False

    def solve_challenge(self, page: Page, timeout: int = 60) -> bool:
        """Attempt to solve DataDome challenge.

        Strategy:
        1. Wait for challenge to load
        2. Find and click the CAPTCHA checkbox
        3. Wait for resolution
        """
        log.info("DataDome challenge detected, attempting to solve...")

        deadline = time.time() + timeout

        # Wait for challenge page to fully load
        time.sleep(3)

        # Try to find and click the CAPTCHA
        while time.time() < deadline:
            try:
                # Look for DataDome CAPTCHA iframe
                iframe = page.frame_locator("iframe[src*='captcha-delivery']")
                if iframe:
                    # Try to click checkbox inside iframe
                    checkbox = iframe.locator("input[type='checkbox'], .captcha__human, #captcha__human__checkbox")
                    if checkbox.count() > 0:
                        checkbox.first.click()
                        time.sleep(3)

                        # Check if solved
                        if not self.is_challenge(page):
                            log.info("DataDome challenge solved")
                            return True

                # Try direct click on any button
                buttons = page.locator("button, input[type='submit'], .captcha__human__checkbox")
                if buttons.count() > 0:
                    buttons.first.click()
                    time.sleep(3)

                    if not self.is_challenge(page):
                        log.info("DataDome challenge solved via button")
                        return True

            except Exception as exc:
                log.debug("Challenge solve attempt failed: %s", exc)

            time.sleep(2)

        log.warning("DataDome challenge solve timeout")
        return False

    def check_and_solve(self, page: Page, timeout: int = 60) -> bool:
        """Check for DataDome challenge and solve if present."""
        if not self.is_challenge(page):
            return True

        return self.solve_challenge(page, timeout)
