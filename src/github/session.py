"""GitHub session management (cookies, auth state)."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

from playwright.sync_api import BrowserContext, Page

log = logging.getLogger(__name__)


def save_cookies(context: BrowserContext, path: str) -> None:
    """Save browser cookies to file."""
    try:
        cookies = context.cookies()
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(json.dumps(cookies, indent=2), encoding="utf-8")
        log.debug("Cookies saved: %s (%d cookies)", path, len(cookies))
    except Exception as exc:
        log.warning("Failed to save cookies: %s", exc)


def load_cookies(context: BrowserContext, path: str) -> bool:
    """Load cookies from file. Returns True if successful."""
    cookie_path = Path(path)
    if not cookie_path.exists():
        return False
    try:
        cookies = json.loads(cookie_path.read_text(encoding="utf-8"))
        context.add_cookies(cookies)
        log.debug("Cookies loaded: %s (%d cookies)", path, len(cookies))
        return True
    except Exception as exc:
        log.warning("Failed to load cookies: %s", exc)
        return False


def is_logged_in(page: Page) -> bool:
    """Check if currently logged into GitHub."""
    try:
        # Check for avatar/profile indicator
        avatar = page.locator('[aria-label="View profile"]')
        if avatar.count() > 0:
            return True

        # Check URL pattern
        if "github.com" in page.url:
            # Try to find user menu
            user_menu = page.locator('[data-testid="user-avatar-menu"]')
            if user_menu.count() > 0:
                return True

        return False
    except Exception:
        return False


def get_username(page: Page) -> Optional[str]:
    """Extract current GitHub username from page."""
    try:
        # Try meta tag
        meta = page.locator('meta[name="user-login"]')
        if meta.count() > 0:
            return meta.get_attribute("content")

        # Try URL
        if "/settings/profile" in page.url:
            return page.url.split("/")[-1]

        return None
    except Exception:
        return None


def save_session(
    page: Page,
    username: str,
    session_dir: str = "data/sessions",
) -> str:
    """Save full session state (cookies + storage)."""
    session_path = Path(session_dir) / f"{username}.json"
    session_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Get cookies
        context = page.context
        cookies = context.cookies()

        # Get localStorage
        storage = page.evaluate("""
            () => {
                const items = {};
                for (let i = 0; i < localStorage.length; i++) {
                    const key = localStorage.key(i);
                    items[key] = localStorage.getItem(key);
                }
                return items;
            }
        """)

        data = {
            "username": username,
            "cookies": cookies,
            "storage": storage,
            "url": page.url,
        }

        session_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        log.info("Session saved: %s", session_path)
        return str(session_path)

    except Exception as exc:
        log.warning("Failed to save session: %s", exc)
        return ""


def load_session(
    context: BrowserContext,
    username: str,
    session_dir: str = "data/sessions",
) -> bool:
    """Load session state into browser context."""
    session_path = Path(session_dir) / f"{username}.json"
    if not session_path.exists():
        return False

    try:
        data = json.loads(session_path.read_text(encoding="utf-8"))

        # Load cookies
        if data.get("cookies"):
            context.add_cookies(data["cookies"])

        log.info("Session loaded for %s", username)
        return True

    except Exception as exc:
        log.warning("Failed to load session: %s", exc)
        return False
