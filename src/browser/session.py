"""Session management — selenium-based."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Optional

log = logging.getLogger(__name__)


class SessionManager:
    """Manages browser session for GitHub automation."""

    def __init__(self, session_dir: str = "data/sessions"):
        self._session_dir = Path(session_dir)
        self._session_dir.mkdir(parents=True, exist_ok=True)
        self._browser: Any = None
        self._driver: Any = None

    def start(
        self,
        headless: bool = False,
        proxy: Optional[str] = None,
    ) -> Any:
        """Start browser and return driver."""
        from src.browser.patchright import PatchrightBrowser

        self._browser = PatchrightBrowser()
        self._driver = self._browser.launch(headless=headless, proxy=proxy)

        # Load saved cookies
        self._load_session()

        return self._driver

    def get_driver(self) -> Any:
        if self._driver is None:
            raise RuntimeError("Session not started")
        return self._driver

    def save_session(self) -> None:
        """Save cookies."""
        if self._driver is None:
            return
        try:
            cookies = self._driver.get_cookies()
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
            if cookies and self._driver:
                for cookie in cookies:
                    try:
                        self._driver.add_cookie(cookie)
                    except Exception:
                        pass
                log.info("Session loaded: %d cookies", len(cookies))
        except Exception as exc:
            log.debug("Failed to load session: %s", exc)

    def close(self) -> None:
        try:
            self.save_session()
        except Exception:
            pass
        if self._browser:
            self._browser.close()
        self._driver = None
        self._browser = None
