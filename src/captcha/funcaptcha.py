"""FunCaptcha (Arkose Labs) solver via CapSolver API — HTTP-based."""

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

    def solve(self, site_url: str, site_key: str, **kwargs) -> Optional[str]:
        """Solve FunCaptcha via CapSolver API."""
        if not self._api_key:
            return None

        api_domain = kwargs.get("api_domain", "")
        return self.solve_async(site_key, site_url, api_domain)

    def solve_async(self, sitekey: str, page_url: str, api_domain: str = "") -> Optional[str]:
        """Solve FunCaptcha via API."""
        if not self._api_key:
            return None

        try:
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
            task_id = str(data.get("taskId", ""))
            log.info("FunCaptcha task created: %s", task_id)

            deadline = time.time() + self._timeout
            while time.time() < deadline:
                time.sleep(3)
                resp = requests.post(f"{CAPSOLVER_API}/getTaskResult", json={
                    "clientKey": self._api_key,
                    "taskId": task_id,
                })
                data = resp.json()
                if data.get("status") == "ready":
                    token = data.get("solution", {}).get("token", "")
                    if token:
                        log.info("FunCaptcha solved")
                        return token

            log.warning("FunCaptcha solve timeout")
            return None

        except Exception as exc:
            log.warning("FunCaptcha solve failed: %s", exc)
            return None
