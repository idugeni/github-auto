"""Cloudflare Turnstile solver (simplified from tokenharbor/alap)."""

from __future__ import annotations

import logging
import random
import time
from typing import Any, Optional

from playwright.sync_api import Page

from .base import CaptchaSolver

log = logging.getLogger(__name__)


class TurnstileSolver(CaptchaSolver):
    """Solve Cloudflare Turnstile CAPTCHA via browser automation."""

    def __init__(self, timeout: int = 180):
        self._timeout = timeout

    def solve(self, page: Page, url: Optional[str] = None) -> Optional[str]:  # noqa: ARG002
        """Solve Turnstile on page. Returns token or None."""
        try:
            return self._solve_invisible(page)
        except Exception as exc:
            log.warning("Turnstile solve failed: %s", exc)
            return None

    def _solve_invisible(self, page: Page) -> Optional[str]:
        deadline = time.time() + self._timeout
        iframe = self._find_turnstile_iframe(page, deadline)
        if not iframe:
            log.debug("No Turnstile iframe found")
            return None

        box: Any = None
        try:
            box = iframe.bounding_box()  # type: ignore[union-attr]
        except Exception:
            pass

        if box:
            for _ in range(30):
                if time.time() > deadline:
                    break
                x = box["x"] + random.uniform(0, box["width"])
                y = box["y"] + random.uniform(0, box["height"])
                page.mouse.move(x, y)
                time.sleep(random.uniform(0.1, 0.3))
                token = self._get_token(page)
                if token:
                    log.info("Turnstile token obtained via mouse movement")
                    return token

        # Try clicking checkbox inside iframe
        try:
            frame_page = iframe  # type: ignore
            checkbox = frame_page.locator("input[type='checkbox'], .cb-lb")  # type: ignore[union-attr]
            if checkbox.count() > 0:
                checkbox.first.click()
                time.sleep(3)
                token = self._get_token(page)
                if token:
                    log.info("Turnstile token obtained via click")
                    return token
        except Exception as exc:
            log.debug("Click attempt failed: %s", exc)

        return None

    def _find_turnstile_iframe(self, page: Page, deadline: float) -> Any:
        selectors = [
            "iframe[src*='challenges.cloudflare.com']",
            "iframe[src*='turnstile']",
            "iframe[title*='Cloudflare']",
        ]
        while time.time() < deadline:
            for selector in selectors:
                try:
                    frames = page.locator(selector)
                    if frames.count() > 0:
                        frame_el = frames.first
                        content = frame_el.content_frame()
                        if content:
                            return content
                except Exception:
                    pass
            time.sleep(1)
        return None

    def _get_token(self, page: Page) -> Optional[str]:
        try:
            token_input = page.locator("[name='cf-turnstile-response']")
            if token_input.count() > 0:
                token = token_input.first.input_value()
                if token and len(token) > 10:
                    return token
        except Exception:
            pass

        try:
            token = page.evaluate("""
                () => {
                    const input = document.querySelector('[name="cf-turnstile-response"]');
                    if (input && input.value) return input.value;
                    if (window.turnstile) return window.turnstile.getResponse();
                    return null;
                }
            """)
            if token and len(str(token)) > 10:
                return str(token)
        except Exception:
            pass

        return None
