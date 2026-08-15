"""FunCaptcha (Arkose Labs) solver via CapSolver."""

from __future__ import annotations

import logging
import os
import time
from typing import Optional

import requests

from .base import CaptchaSolver

log = logging.getLogger(__name__)

CAPSOLVER_API = os.getenv("CAPSOLVER_API_URL", "https://api.capsolver.com")


class FunCaptchaSolver(CaptchaSolver):
    """Solve FunCaptcha (Arkose Labs) via CapSolver API."""

    def __init__(self, api_key: Optional[str] = None, timeout: int = 180):
        self._api_key = api_key or os.getenv("CAPSOLVER_API_KEY", "")
        self._timeout = timeout

        if not self._api_key:
            log.warning("No CAPSOLVER_API_KEY, FunCaptcha solving disabled")

    def _create_task(self, sitekey: str, page_url: str, api_domain: str = "") -> str:
        """Create FunCaptcha solving task."""
        task = {
            "type": "FunCaptchaTaskProxyLess",
            "websiteURL": page_url,
            "websitePublicKey": sitekey,
        }
        if api_domain:
            task["websiteSubDomain"] = api_domain

        resp = requests.post(f"{CAPSOLVER_API}/createTask", json={
            "clientKey": self._api_key,
            "task": task,
        })
        data = resp.json()
        if data.get("errorId", 0) != 0:
            raise RuntimeError(f"CapSolver error: {data.get('errorDescription', '')}")
        return str(data.get("taskId", ""))

    def _get_result(self, task_id: str) -> str:
        """Get task result."""
        resp = requests.post(f"{CAPSOLVER_API}/getTaskResult", json={
            "clientKey": self._api_key,
            "taskId": task_id,
        })
        data = resp.json()
        if data.get("status") == "ready":
            return data.get("solution", {}).get("token", "")
        return ""

    def solve(self, page: 'Page', url: Optional[str] = None) -> Optional[str]:
        """Solve FunCaptcha on page."""
        if not self._api_key:
            return None

        # Extract sitekey from page
        try:
            sitekey = page.evaluate("""
                () => {
                    const el = document.querySelector('[data-fun-captcha-widget-id]') ||
                               document.querySelector('iframe[src*="arkoselabs"]');
                    if (el) {
                        return el.getAttribute('data-sitekey') ||
                               new URL(el.src).searchParams.get('sitekey') ||
                               new URL(el.src).searchParams.get('public_key');
                    }
                    return null;
                }
            """)
        except Exception:
            sitekey = None

        if not sitekey:
            log.warning("No FunCaptcha sitekey found")
            return None

        return self.solve_async(sitekey, page.url)

    def solve_async(self, sitekey: str, page_url: str, api_domain: str = "") -> Optional[str]:
        """Solve FunCaptcha via API."""
        if not self._api_key:
            return None

        try:
            task_id = self._create_task(sitekey, page_url, api_domain)
            log.info("FunCaptcha task created: %s", task_id)

            deadline = time.time() + self._timeout
            while time.time() < deadline:
                time.sleep(3)
                result = self._get_result(task_id)
                if result:
                    log.info("FunCaptcha solved")
                    return result

            log.warning("FunCaptcha solve timeout")
            return None

        except Exception as exc:
            log.warning("FunCaptcha solve failed: %s", exc)
            return None
