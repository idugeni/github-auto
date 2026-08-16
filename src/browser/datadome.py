"""DataDome bypass — detect and wait for manual solve if needed."""

from __future__ import annotations

import logging
import time
from typing import Optional

from playwright.sync_api import Page

log = logging.getLogger(__name__)


class DataDomeBypass:
    """Handle DataDome challenges."""

    def __init__(self):
        self._solved = False

    def is_challenge(self, page: Page) -> bool:
        """Check for DataDome challenge."""
        try:
            url = page.url
            if "captcha-delivery.com" in url or "datadome" in url:
                return True
            for frame in page.frames:
                if "captcha-delivery.com" in (frame.url or ""):
                    return True
        except Exception:
            pass
        return False

    def wait_for_solve(self, page: Page, timeout: int = 120) -> bool:
        """Wait for DataDome challenge to be solved (manual or auto).

        Returns True if challenge resolved within timeout.
        """
        if not self.is_challenge(page):
            return True

        log.info("DataDome challenge detected, waiting for solve...")
        deadline = time.time() + timeout

        while time.time() < deadline:
            time.sleep(2)
            if not self.is_challenge(page):
                log.info("DataDome challenge resolved")
                self._solved = True
                return True

        log.warning("DataDome challenge timeout")
        return False

    def check_and_wait(self, page: Page, timeout: int = 120) -> bool:
        """Check and wait if needed."""
        return self.wait_for_solve(page, timeout)
