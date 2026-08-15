"""hCaptcha solver integration."""

from __future__ import annotations

import logging
import os
import time
from typing import Optional

import requests

from .base import CaptchaSolver

log = logging.getLogger(__name__)

CAPTCHA_SOLVER_APIS = {
    "capmonster": "https://api.capmonster.cloud",
    "2captcha": "https://api.2captcha.com",
    "anticaptcha": "https://api.anti-captcha.com",
}


class HCaptchaSolver(CaptchaSolver):
    """Solve hCaptcha via third-party CAPTCHA solving service.

    Supports CapMonster, 2Captcha, and AntiCaptcha.
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
        self._base_url = CAPTCHA_SOLVER_APIS.get(service, "")

        if not self._api_key:
            log.warning("No API key for %s, hCaptcha solving disabled", service)

    def _create_task(self, sitekey: str, page_url: str) -> str:
        """Create CAPTCHA solving task."""
        if self._service == "capmonster":
            return self._create_capmonster_task(sitekey, page_url)
        elif self._service == "2captcha":
            return self._create_2captcha_task(sitekey, page_url)
        elif self._service == "anticaptcha":
            return self._create_anticaptcha_task(sitekey, page_url)
        else:
            raise ValueError(f"Unknown service: {self._service}")

    def _create_capmonster_task(self, sitekey: str, page_url: str) -> str:
        """Create CapMonster task."""
        resp = requests.post(f"{self._base_url}/createTask", json={
            "clientKey": self._api_key,
            "task": {
                "type": "HCaptchaTaskProxyless",
                "websiteURL": page_url,
                "websiteKey": sitekey,
            },
        })
        if resp.status_code != 200:
            raise RuntimeError(f"CapMonster task creation failed: {resp.text}")
        data = resp.json()
        if data.get("errorId", 0) != 0:
            raise RuntimeError(f"CapMonster error: {data.get('errorDescription', '')}")
        return str(data.get("taskId", ""))

    def _create_2captcha_task(self, sitekey: str, page_url: str) -> str:
        """Create 2Captcha task."""
        resp = requests.post(f"{self._base_url}/in.php", data={
            "key": self._api_key,
            "method": "hcaptcha",
            "sitekey": sitekey,
            "pageurl": page_url,
            "json": 1,
        })
        if resp.status_code != 200:
            raise RuntimeError(f"2Captcha task creation failed: {resp.text}")
        data = resp.json()
        if data.get("status") != 1:
            raise RuntimeError(f"2Captcha error: {data.get('request', '')}")
        return str(data.get("request", ""))

    def _create_anticaptcha_task(self, sitekey: str, page_url: str) -> str:
        """Create AntiCaptcha task."""
        resp = requests.post(f"{self._base_url}/createTask", json={
            "clientKey": self._api_key,
            "task": {
                "type": "HCaptchaTaskProxyless",
                "websiteURL": page_url,
                "websiteKey": sitekey,
            },
        })
        if resp.status_code != 200:
            raise RuntimeError(f"AntiCaptcha task creation failed: {resp.text}")
        data = resp.json()
        if data.get("errorId", 0) != 0:
            raise RuntimeError(f"AntiCaptcha error: {data.get('errorDescription', '')}")
        return str(data.get("taskId", ""))

    def _get_result(self, task_id: str) -> str:
        """Get task result."""
        if self._service == "capmonster":
            return self._get_capmonster_result(task_id)
        elif self._service == "2captcha":
            return self._get_2captcha_result(task_id)
        elif self._service == "anticaptcha":
            return self._get_anticaptcha_result(task_id)
        else:
            raise ValueError(f"Unknown service: {self._service}")

    def _get_capmonster_result(self, task_id: str) -> str:
        """Get CapMonster result."""
        resp = requests.post(f"{self._base_url}/getTaskResult", json={
            "clientKey": self._api_key,
            "taskId": task_id,
        })
        data = resp.json()
        if data.get("status") == "ready":
            return data.get("solution", {}).get("gRecaptchaResponse", "")
        return ""

    def _get_2captcha_result(self, task_id: str) -> str:
        """Get 2Captcha result."""
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

    def _get_anticaptcha_result(self, task_id: str) -> str:
        """Get AntiCaptcha result."""
        resp = requests.post(f"{self._base_url}/getTaskResult", json={
            "clientKey": self._api_key,
            "taskId": task_id,
        })
        data = resp.json()
        if data.get("status") == "ready":
            return data.get("solution", {}).get("gRecaptchaResponse", "")
        return ""

    def solve(self, page: 'Page', url: Optional[str] = None) -> Optional[str]:
        """Solve hCaptcha on page.

        Note: This requires the page to have hCaptcha widget.
        For API-only solving, use solve_async() instead.
        """
        if not self._api_key:
            log.warning("No API key configured for hCaptcha solving")
            return None

        # Extract sitekey from page
        try:
            sitekey = page.evaluate("""
                () => {
                    const el = document.querySelector('[data-hcaptcha-widget-id]') ||
                               document.querySelector('iframe[src*="hcaptcha"]');
                    if (el) {
                        return el.getAttribute('data-sitekey') ||
                               new URL(el.src).searchParams.get('sitekey');
                    }
                    return null;
                }
            """)
        except Exception:
            sitekey = None

        if not sitekey:
            log.warning("No hCaptcha sitekey found on page")
            return None

        page_url = page.url
        return self.solve_async(sitekey, page_url)

    def solve_async(self, sitekey: str, page_url: str) -> Optional[str]:
        """Solve hCaptcha via API (no browser needed)."""
        if not self._api_key:
            return None

        try:
            task_id = self._create_task(sitekey, page_url)
            log.info("hCaptcha task created: %s", task_id)

            # Poll for result
            deadline = time.time() + self._timeout
            while time.time() < deadline:
                time.sleep(3)
                result = self._get_result(task_id)
                if result:
                    log.info("hCaptcha solved")
                    return result

            log.warning("hCaptcha solve timeout")
            return None

        except Exception as exc:
            log.warning("hCaptcha solve failed: %s", exc)
            return None
