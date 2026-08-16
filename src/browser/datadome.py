"""DataDome bypass — CapSolver integration."""

from __future__ import annotations

import logging
import os
import re
import time
from typing import Optional

import requests
from playwright.sync_api import Page

log = logging.getLogger(__name__)

CAPSOLVER_API = "https://api.capsolver.com"
CAPSOLVER_KEY = os.getenv("CAPSOLVER_API_KEY", "")


class DataDomeBypass:
    """Handle DataDome challenges via CapSolver."""

    def __init__(self):
        self._solved = False

    def is_challenge(self, page: Page) -> bool:
        """Check for DataDome challenge."""
        try:
            url = page.url
            if "captcha-delivery.com" in url or "datadome" in url:
                return True
            for frame in page.frames:
                if "captcha-delivery.com" in (frame.url or ""):
                    return True
        except Exception:
            pass
        return False

    def wait_for_solve(self, page: Page, timeout: int = 120) -> bool:
        """Wait for DataDome challenge to be solved."""
        if not self.is_challenge(page):
            return True

        log.info("DataDome challenge detected, solving via CapSolver...")

        # Try CapSolver if available
        if CAPSOLVER_KEY:
            return self._solve_with_capsolver(page, timeout)

        # Fallback: manual wait
        log.info("No CapSolver key, waiting for manual solve...")
        deadline = time.time() + timeout
        while time.time() < deadline:
            time.sleep(2)
            if not self.is_challenge(page):
                log.info("DataDome solved manually")
                return True
        return False

    def _solve_with_capsolver(self, page: Page, timeout: int) -> bool:
        """Solve DataDome via CapSolver."""
        # Get page URL
        page_url = page.url

        # Try to find sitekey from page
        sitekey = self._extract_sitekey(page)
        if not sitekey:
            log.warning("No sitekey found, using default")
            sitekey = "0x4AAAAAAADnPIDROrmt1Wwj"  # Common DataDome sitekey

        # Create task
        try:
            resp = requests.post(f"{CAPSOLVER_API}/createTask", json={
                "clientKey": CAPSOLVER_KEY,
                "task": {
                    "type": "AntiTurnstileTaskProxyLess",
                    "websiteURL": page_url,
                    "websiteKey": sitekey,
                },
            }, timeout=30)
            data = resp.json()

            if data.get("errorId", 0) != 0:
                log.warning("CapSolver error: %s", data.get("errorDescription"))
                return False

            task_id = data.get("taskId")
            log.info("CapSolver task: %s", task_id)

        except Exception as exc:
            log.warning("CapSolver request failed: %s", exc)
            return False

        # Poll for result
        deadline = time.time() + timeout
        while time.time() < deadline:
            time.sleep(3)
            try:
                resp = requests.post(f"{CAPSOLVER_API}/getTaskResult", json={
                    "clientKey": CAPSOLVER_KEY,
                    "taskId": task_id,
                }, timeout=30)
                data = resp.json()

                if data.get("status") == "ready":
                    token = data.get("solution", {}).get("token", "")
                    if token:
                        log.info("CapSolver solved DataDome")
                        return self._inject_token(page, token)

                if data.get("status") == "failed":
                    log.warning("CapSolver task failed")
                    return False

            except Exception as exc:
                log.debug("CapSolver poll error: %s", exc)

        log.warning("CapSolver timeout")
        return False

    def _extract_sitekey(self, page: Page) -> Optional[str]:
        """Extract sitekey from page."""
        try:
            for frame in page.frames:
                url = frame.url or ""
                if "captcha-delivery.com" in url:
                    match = re.search(r"sitekey=([^&]+)", url)
                    if match:
                        return match.group(1)

                    # Try from content
                    content = frame.content()
                    if content:
                        match = re.search(r'data-sitekey="([^"]+)"', content)
                        if match:
                            return match.group(1)
        except Exception:
            pass
        return None

    def _inject_token(self, page: Page, token: str) -> bool:
        """Inject CAPTCHA token."""
        try:
            # Find DataDome iframe
            for frame in page.frames:
                if "captcha-delivery.com" in (frame.url or ""):
                    # Try to submit token
                    frame.evaluate(f"""
                        const input = document.querySelector('[name="cf-turnstile-response"]') ||
                                      document.querySelector('textarea[name*="captcha"]');
                        if (input) {{
                            input.value = '{token}';
                            input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        }}
                        const form = document.querySelector('form');
                        if (form) form.submit();
                    """)
                    time.sleep(5)
                    return not self.is_challenge(page)
        except Exception as exc:
            log.debug("Token injection failed: %s", exc)
        return False

    def check_and_wait(self, page: Page, timeout: int = 120) -> bool:
        """Check and wait if needed."""
        return self.wait_for_solve(page, timeout)
