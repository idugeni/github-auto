"""FunCaptcha (Arkose Labs) solver integration."""

from __future__ import annotations

import logging
import os
import time
from typing import Optional

import requests

from .base import CaptchaSolver

log = logging.getLogger(__name__)


class FunCaptchaSolver(CaptchaSolver):
    """Solve FunCaptcha (Arkose Labs) via third-party service.

    Supports CapMonster and 2Captcha.
    """

    def __init__(
        self,
        service: str = "capmonster",
        api_key: Optional[str] = None,
        timeout: int = 180,
    ):
        self._service = service
        self._api_key = api_key or os.getenv(f"{service.upper()}_API_KEY", "")
        self._timeout = timeout

        if service == "capmonster":
            self._base_url = "https://api.capmonster.cloud"
        elif service == "2captcha":
            self._base_url = "https://api.2captcha.com"
        else:
            raise ValueError(f"Unsupported service: {service}")

    def _create_task(self, sitekey: str, page_url: str, api_domain: str = "") -> str:
        """Create FunCaptcha solving task."""
        if self._service == "capmonster":
            task = {
                "type": "FunCaptchaTaskProxyless",
                "websiteURL": page_url,
                "websitePublicKey": sitekey,
            }
            if api_domain:
                task["websiteSubDomain"] = api_domain

            resp = requests.post(f"{self._base_url}/createTask", json={
                "clientKey": self._api_key,
                "task": task,
            })
            data = resp.json()
            if data.get("errorId", 0) != 0:
                raise RuntimeError(f"CapMonster error: {data.get('errorDescription', '')}")
            return str(data.get("taskId", ""))

        elif self._service == "2captcha":
            resp = requests.post(f"{self._base_url}/in.php", data={
                "key": self._api_key,
                "method": "funcaptcha",
                "sitekey": sitekey,
                "pageurl": page_url,
                "json": 1,
            })
            data = resp.json()
            if data.get("status") != 1:
                raise RuntimeError(f"2Captcha error: {data.get('request', '')}")
            return str(data.get("request", ""))

        raise ValueError(f"Unknown service: {self._service}")

    def _get_result(self, task_id: str) -> str:
        """Get task result."""
        if self._service == "capmonster":
            resp = requests.post(f"{self._base_url}/getTaskResult", json={
                "clientKey": self._api_key,
                "taskId": task_id,
            })
            data = resp.json()
            if data.get("status") == "ready":
                return data.get("solution", {}).get("token", "")
            return ""

        elif self._service == "2captcha":
            resp = requests.get(f"{self._base_url}/res.php", params={
                "key": self._api_key,
                "action": "get",
                "id": task_id,
                "json": 1,
            })
            data = resp.json()
            if data.get("status") == 1:
                return data.get("request", "")
            return ""

        return ""

    def solve(self, page: 'Page', url: Optional[str] = None) -> Optional[str]:
        """Solve FunCaptcha on page."""
        if not self._api_key:
            log.warning("No API key configured for FunCaptcha solving")
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
            log.warning("No FunCaptcha sitekey found on page")
            return None

        page_url = page.url
        return self.solve_async(sitekey, page_url)

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
