"""Patchright browser driver (undetected Chromium)."""

from __future__ import annotations

import logging
import random
from typing import Any, Optional

from .base import BrowserDriver
from .stealth import CHROME_ARGS, apply_stealth

log = logging.getLogger(__name__)


class PatchrightBrowser(BrowserDriver):
    """Patchright — undetected Chromium via Playwright fork."""

    def __init__(self):
        self._pw = None
        self._browser = None

    def launch(
        self,
        headless: bool = False,
        proxy: Optional[str] = None,
        viewport_width: int = 1280,
        viewport_height: int = 720,
    ) -> Any:
        try:
            from patchright.sync_api import sync_playwright as patchright_sync
            pw_mod = patchright_sync().start()
        except ImportError:
            log.warning("patchright not installed, falling back to playwright")
            from playwright.sync_api import sync_playwright
            pw_mod = sync_playwright().start()

        self._pw = pw_mod

        launch_args: dict[str, Any] = {
            "headless": headless,
            "args": CHROME_ARGS,
        }
        if proxy:
            launch_args["proxy"] = {"server": proxy}

        self._browser = pw_mod.chromium.launch(**launch_args)
        ctx = self._browser.new_context(
            viewport={"width": viewport_width, "height": viewport_height},
            user_agent=_get_chrome_ua(),
        )
        ctx.on("page", lambda page: apply_stealth(page))
        ctx.set_default_timeout(60_000)
        return ctx

    def close(self) -> None:
        if self._browser:
            try:
                self._browser.close()
            except Exception:
                pass
            self._browser = None
        if self._pw:
            try:
                self._pw.stop()
            except Exception:
                pass
            self._pw = None


def _get_chrome_ua() -> str:
    major = random.randint(126, 132)
    build = random.randint(6000, 6999)
    patch = random.randint(0, 149)
    return (
        f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        f"AppleWebKit/537.36 (KHTML, like Gecko) "
        f"Chrome/{major}.0.{build}.{patch} Safari/537.36"
    )
