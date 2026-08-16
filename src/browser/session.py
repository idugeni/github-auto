"""Session management for GitHub automation.

Ensures all operations run in the same browser session
to avoid bot detection.
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Optional

from playwright.sync_api import Browser, BrowserContext, Page

from config.settings import config

log = logging.getLogger(__name__)


class SessionManager:
    """Manages browser session for GitHub automation.

    Key principle: ONE session throughout the entire flow.
    This prevents bot detection from session mismatches.
    """

    def __init__(self, session_dir: str = "data/sessions"):
        self._session_dir = Path(session_dir)
        self._session_dir.mkdir(parents=True, exist_ok=True)
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None

    def start(
        self,
        headless: Optional[bool] = None,
        proxy: Optional[str] = None,
        viewport_width: int = 1280,
        viewport_height: int = 720,
    ) -> Page:
        """Start browser session and return page.

        Uses patchright (undetected Chromium) with xvfb on Linux.
        """
        from patchright.sync_api import sync_playwright

        is_headless = headless if headless is not None else config.browser.headless

        log.info("Starting browser session (headless=%s)", is_headless)

        self._pw = sync_playwright().start()

        # Launch browser with stealth settings
        launch_args = [
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
            "--disable-webrtc",
            "--disable-extensions",
            "--window-size=1920,1080",
        ]

        self._browser = self._pw.chromium.launch(
            headless=is_headless,
            args=launch_args,
        )

        # Create context with realistic settings
        context_args = {
            "viewport": {"width": viewport_width, "height": viewport_height},
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "locale": "en-US",
            "timezone_id": "America/New_York",
        }

        if proxy:
            context_args["proxy"] = {"server": proxy}

        self._context = self._browser.new_context(**context_args)

        # Load existing cookies if available
        self._load_session()

        self._page = self._context.new_page()

        # Apply stealth
        from .stealth import apply_stealth
        apply_stealth(self._page)

        log.info("Browser session started")
        return self._page

    def get_page(self) -> Page:
        """Get current page."""
        if self._page is None:
            raise RuntimeError("Session not started")
        return self._page

    def get_context(self) -> BrowserContext:
        """Get current context."""
        if self._context is None:
            raise RuntimeError("Session not started")
        return self._context

    def save_session(self) -> None:
        """Save session cookies and state."""
        if self._context is None:
            return

        try:
            cookies = self._context.cookies()
            session_file = self._session_dir / "github_session.json"
            session_file.write_text(
                json.dumps(cookies, indent=2),
                encoding="utf-8",
            )
            log.info("Session saved: %d cookies", len(cookies))
        except Exception as exc:
            log.debug("Failed to save session: %s", exc)

    def _load_session(self) -> None:
        """Load session cookies."""
        session_file = self._session_dir / "github_session.json"
        if not session_file.exists():
            return

        try:
            cookies = json.loads(session_file.read_text(encoding="utf-8"))
            if cookies:
                self._context.add_cookies(cookies)
                log.info("Session loaded: %d cookies", len(cookies))
        except Exception as exc:
            log.debug("Failed to load session: %s", exc)

    def close(self) -> None:
        """Close browser session."""
        try:
            self.save_session()
        except Exception:
            pass

        if self._page:
            try:
                self._page.close()
            except Exception:
                pass

        if self._context:
            try:
                self._context.close()
            except Exception:
                pass

        if self._browser:
            try:
                self._browser.close()
            except Exception:
                pass

        if hasattr(self, '_pw') and self._pw:
            try:
                self._pw.stop()
            except Exception:
                pass

        self._page = None
        self._context = None
        self._browser = None
        log.info("Browser session closed")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
