"""Session management — camoufox headless."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Optional

log = logging.getLogger(__name__)


class SessionManager:
    """Manages camoufox browser session."""

    def __init__(self, session_dir: str = "data/sessions"):
        self._session_dir = Path(session_dir)
        self._session_dir.mkdir(parents=True, exist_ok=True)
        self._driver = None
        self._page = None

    def start(
        self,
        headless: bool = True,
        proxy: Optional[str] = None,
    ) -> Any:
        """Start camoufox and return page."""
        from src.browser.camoufox import CamoufoxBrowser

        self._driver = CamoufoxBrowser()
        context = self._driver.launch(headless=headless, proxy=proxy)
        self._page = context.new_page()

        # Load saved cookies
        self._load_session()

        return self._page

    def get_page(self) -> Any:
        if self._page is None:
            raise RuntimeError("Session not started")
        return self._page

    def save_session(self) -> None:
        """Save cookies."""
        if self._page is None:
            return
        try:
            context = self._page.context
            cookies = context.cookies()
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
            if cookies and self._page:
                self._page.context.add_cookies(cookies)
                log.info("Session loaded: %d cookies", len(cookies))
        except Exception as exc:
            log.debug("Failed to load session: %s", exc)

    def close(self) -> None:
        try:
            self.save_session()
        except Exception:
            pass
        if self._driver:
            self._driver.close()
        self._page = None
        self._driver = None
