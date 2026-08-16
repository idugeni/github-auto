"""Patchright browser driver — undetected Chromium.

Uses patchright for anti-detection.
Runs with xvfb on Linux for headless display.
"""

from __future__ import annotations

import logging
import os
import subprocess
import time
from typing import Optional

from patchright.sync_api import sync_playwright, Browser, BrowserContext, Page

log = logging.getLogger(__name__)


class PatchrightBrowser:
    """Patchright browser with anti-detection."""

    def __init__(self):
        self._pw = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
        self._xvfb_proc = None

    def _start_xvfb(self) -> None:
        """Start Xvfb virtual display on Linux."""
        if os.name != "nt":  # Not Windows
            try:
                self._xvfb_proc = subprocess.Popen(
                    ["Xvfb", ":99", "-screen", "0", "1920x1080x24", "-nolisten", "tcp"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                os.environ["DISPLAY"] = ":99"
                time.sleep(1)
                log.info("Xvfb started on :99")
            except FileNotFoundError:
                log.warning("Xvfb not found, using default display")

    def _stop_xvfb(self) -> None:
        """Stop Xvfb virtual display."""
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
        viewport_width: int = 1280,
        viewport_height: int = 720,
    ) -> Page:
        """Launch browser and return page.

        On Linux, uses Xvfb for headless display.
        """
        # Start Xvfb on Linux if not headless
        if not headless:
            self._start_xvfb()

        self._pw = sync_playwright().start()

        # Launch args for anti-detection
        args = [
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
            "--disable-webrtc",
            "--disable-extensions",
            "--window-size=1920,1080",
        ]

        self._browser = self._pw.chromium.launch(
            headless=headless,
            args=args,
        )

        # Create context
        context_args = {
            "viewport": {"width": viewport_width, "height": viewport_height},
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "locale": "en-US",
            "timezone_id": "America/New_York",
        }

        if proxy:
            context_args["proxy"] = {"server": proxy}

        self._context = self._browser.new_context(**context_args)
        self._page = self._context.new_page()

        log.info("Browser launched (headless=%s)", headless)
        return self._page

    def get_context(self) -> BrowserContext:
        """Get browser context."""
        if self._context is None:
            raise RuntimeError("Browser not launched")
        return self._context

    def close(self) -> None:
        """Close browser."""
        try:
            if self._page:
                self._page.close()
        except Exception:
            pass

        try:
            if self._context:
                self._context.close()
        except Exception:
            pass

        try:
            if self._browser:
                self._browser.close()
        except Exception:
            pass

        try:
            if self._pw:
                self._pw.stop()
        except Exception:
            pass

        self._stop_xvfb()

        self._page = None
        self._context = None
        self._browser = None
        self._pw = None
        log.info("Browser closed")
