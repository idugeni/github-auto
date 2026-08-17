"""hCaptcha solver via CapSolver API — HTTP-based."""

from __future__ import annotations

import logging
import os
import time
from typing import Optional

import requests

from .base import CaptchaSolver

log = logging.getLogger(__name__)

CAPSOLVER_API = os.getenv("CAPSOLVER_API_URL", "https://api.capsolver.com")


class HCaptchaSolver(CaptchaSolver):
    """Solve hCaptcha via CapSolver API."""

    def __init__(self, api_key: Optional[str] = None, timeout: int = 180):
        self._api_key = api_key or os.getenv("CAPSOLVER_API_KEY", "")
        self._timeout = timeout

        if not self._api_key:
            log.warning("No CAPSOLVER_API_KEY, hCaptcha solving disabled")

    def solve(self, site_url: str, site_key: str, **kwargs) -> Optional[str]:
        """Solve hCaptcha via CapSolver API."""
        if not self._api_key:
            return None

        return self.solve_async(site_key, site_url)

    def solve_async(self, sitekey: str, page_url: str) -> Optional[str]:
        """Solve hCaptcha via API."""
        if not self._api_key:
            return None

        try:
            resp = requests.post(f"{CAPSOLVER_API}/createTask", json={
                "clientKey": self._api_key,
                "task": {
                    "type": "HCaptchaTaskProxyLess",
                    "websiteURL": page_url,
                    "websiteKey": sitekey,
                },
            })
            data = resp.json()
            if data.get("errorId", 0) != 0:
                raise RuntimeError(f"CapSolver error: {data.get('errorDescription', '')}")
            task_id = str(data.get("taskId", ""))
            log.info("hCaptcha task created: %s", task_id)

            deadline = time.time() + self._timeout
            while time.time() < deadline:
                time.sleep(3)
                resp = requests.post(f"{CAPSOLVER_API}/getTaskResult", json={
                    "clientKey": self._api_key,
                    "taskId": task_id,
                })
                data = resp.json()
                if data.get("status") == "ready":
                    token = data.get("solution", {}).get("gRecaptchaResponse", "")
                    if token:
                        log.info("hCaptcha solved")
                        return token

            log.warning("hCaptcha solve timeout")
            return None

        except Exception as exc:
            log.warning("hCaptcha solve failed: %s", exc)
            return None
