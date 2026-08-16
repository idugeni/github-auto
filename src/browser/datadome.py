"""DataDome bypass — selenium-based detection."""

from __future__ import annotations

import logging
import time

log = logging.getLogger(__name__)


class DataDomeBypass:
    """Handle DataDome challenges."""

    def __init__(self):
        self._solved = False

    def is_driver_blocked(self, driver) -> bool:
        """Check if driver shows DataDome challenge."""
        try:
            url = driver.current_url or ""
            if "captcha-delivery.com" in url or "datadome" in url:
                return True
            html = driver.page_source[:1000].lower()
            if "datadome" in html or "captcha-delivery" in html:
                return True
        except Exception:
            pass
        return False

    def wait_for_solve_driver(self, driver, timeout: int = 120) -> bool:
        """Wait for DataDome challenge to resolve."""
        if not self.is_driver_blocked(driver):
            return True

        log.info("DataDome challenge detected, waiting...")
        deadline = time.time() + timeout

        while time.time() < deadline:
            time.sleep(2)
            if not self.is_driver_blocked(driver):
                log.info("DataDome challenge resolved")
                self._solved = True
                return True

        log.warning("DataDome challenge timeout")
        return False
