"""Camoufox browser driver (anti-detection Firefox)."""

from __future__ import annotations

import logging
from typing import Any, Optional

from .base import BrowserDriver

log = logging.getLogger(__name__)


class CamoufoxBrowser(BrowserDriver):
    """Camoufox browser with built-in anti-fingerprinting."""

    def __init__(self):
        self._cm = None

    def launch(
        self,
        headless: bool = False,
        proxy: Optional[str] = None,
        viewport_width: int = 1280,
        viewport_height: int = 720,
    ) -> Any:
        from camoufox.sync_api import Camoufox

        kwargs: dict[str, Any] = {
            "headless": headless,
            "fingerprint_preset": True,
            "geoip": True,
        }
        if proxy:
            kwargs["proxy"] = {"server": proxy}

        self._cm = Camoufox(**kwargs)
        ctx = self._cm.__enter__()
        try:
            ctx.set_default_timeout(60_000)
        except Exception:
            pass
        return ctx

    def close(self) -> None:
        if self._cm:
            try:
                self._cm.__exit__(None, None, None)
            except Exception:
                pass
            self._cm = None
