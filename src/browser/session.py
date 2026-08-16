"""Session management — single session throughout flow."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Optional

from playwright.sync_api import Page

log = logging.getLogger(__name__)


class SessionManager:
    """Manages browser session for GitHub automation."""

    def __init__(self, session_dir: str = "data/sessions"):
        self._session_dir = Path(session_dir)
        self._session_dir.mkdir(parents=True, exist_ok=True)
        self._browser: Any = None
        self._page: Optional[Page] = None
        self._context: Any = None

    def start(
        self,
        headless: bool = False,
        proxy: Optional[str] = None,
    ) -> Page:
        """Start browser and return page."""
        from src.browser.patchright import PatchrightBrowser

        self._browser = PatchrightBrowser()
        self._page = self._browser.launch(headless=headless, proxy=proxy)
        self._context = self._browser.get_context()

        self._load_session()
        return self._page

    def get_page(self) -> Page:
        if self._page is None:
            raise RuntimeError("Session not started")
        return self._page

    def get_context(self) -> Any:
        if self._context is None:
            raise RuntimeError("Session not started")
        return self._context

    def save_session(self) -> None:
        """Save cookies."""
        if self._context is None:
            return
        try:
            cookies = self._context.cookies()
            session_file = self._session_dir / "github_session.json"
            session_file.write_text(json.dumps(cookies, indent=2), encoding="utf-8")
            log.info("Session saved: %d cookies", len(cookies))
        except Exception as exc:
            log.debug("Failed to save session: %s", exc)

    def _load_session(self) -> None:
        """Load cookies."""
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
        """Close browser."""
        try:
            self.save_session()
        except Exception:
            pass
        if self._browser:
            self._browser.close()
        self._page = None
        self._context = None
        self._browser = None
