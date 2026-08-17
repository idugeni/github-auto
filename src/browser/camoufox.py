"""Camoufox browser — headless anti-fingerprint bypass.

Uses Firefox-based Camoufox for deep stealth.
Bypasses DataDome via real Firefox fingerprint.
"""

from __future__ import annotations

import logging
from typing import Optional

log = logging.getLogger(__name__)


class CamoufoxBrowser:
    """Camoufox browser driver — headless mode."""

    def __init__(self):
        self._cm = None
        self._browser = None
        self._context = None

    def launch(
        self,
        headless: bool = True,
        proxy: Optional[str] = None,
    ):
        """Launch Camoufox browser, return BrowserContext."""
        from camoufox.sync_api import Camoufox

        launch_opts = {"headless": headless}
        if proxy:
            launch_opts["proxy"] = {"server": proxy}

        self._cm = Camoufox(**launch_opts)
        self._browser = self._cm.__enter__()

        # Camoufox returns Browser or BrowserContext
        if hasattr(self._browser, "new_context"):
            self._context = self._browser.new_context(
                viewport={"width": 1920, "height": 1080},
                locale="en-US",
            )
        else:
            # Already a BrowserContext
            self._context = self._browser

        log.info("Camoufox launched (headless=%s)", headless)
        return self._context

    def new_page(self):
        """Create new page in context."""
        if not self._context:
            raise RuntimeError("Browser not launched")
        return self._context.new_page()

    def close(self) -> None:
        """Close browser."""
        try:
            if self._context:
                self._context.close()
        except Exception:
            pass
        try:
            if self._cm:
                self._cm.__exit__(None, None, None)
        except Exception:
            pass
        self._context = None
        self._browser = None
        self._cm = None
        log.info("Camoufox closed")
