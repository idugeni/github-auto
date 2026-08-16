"""Browser driver — undetected-chromedriver.

Key: Uses uc which bypasses DataDome/Cloudflare bot detection.
"""

from __future__ import annotations

import logging
import os
import subprocess
import time
from typing import Optional

log = logging.getLogger(__name__)


class PatchrightBrowser:
    """Undetected Chrome browser."""

    def __init__(self):
        self._driver = None
        self._xvfb_proc = None

    def _start_xvfb(self) -> None:
        """Start Xvfb on Linux."""
        if os.name != "nt":
            try:
                self._xvfb_proc = subprocess.Popen(
                    ["Xvfb", ":99", "-screen", "0", "1920x1080x24", "-nolisten", "tcp"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                os.environ["DISPLAY"] = ":99"
                time.sleep(1)
                log.info("Xvfb started")
            except FileNotFoundError:
                log.warning("Xvfb not found")

    def _stop_xvfb(self) -> None:
        if self._xvfb_proc:
            try:
                self._xvfb_proc.terminate()
                self._xvfb_proc.wait(timeout=5)
            except Exception:
                pass
            self._xvfb_proc = None

    def launch(
        self,
        headless: bool = False,
        proxy: Optional[str] = None,
        viewport_width: int = 1920,
        viewport_height: int = 1080,
    ):
        """Launch undetected Chrome."""
        import undetected_chromedriver as uc

        if not headless:
            self._start_xvfb()

        opts = uc.ChromeOptions()
        opts.add_argument(f"--window-size={viewport_width},{viewport_height}")
        opts.add_argument("--no-first-run")
        opts.add_argument("--no-default-browser-check")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--lang=en-US")

        if proxy:
            opts.add_argument(f"--proxy-server={proxy}")
            opts.add_argument("--proxy-bypass-list=<-loopback>")

        self._driver = uc.Chrome(
            options=opts,
            headless=headless,
            use_subprocess=True,
        )
        self._driver.set_page_load_timeout(60)

        log.info("Browser launched (headless=%s)", headless)
        return self._driver

    def get_context(self):
        """Not used with selenium."""
        return None

    def close(self) -> None:
        if self._driver:
            try:
                self._driver.quit()
            except Exception:
                pass
        self._stop_xvfb()
        self._driver = None
        log.info("Browser closed")
