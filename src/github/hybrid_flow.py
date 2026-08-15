"""Hybrid GitHub signup flow — API-first, browser fallback.

Strategy:
1. Try API-only (fastest, ~5s per account)
2. If blocked/challenged → fallback to browser (stealth)
3. If browser also blocked → skip account

This maximizes speed while maintaining success rate.
"""

from __future__ import annotations

import logging
import random
import time
from typing import Optional

from config.settings import config
from src.email.manager import EmailManager
from src.proxy.manager import ProxyManager

from .api_client import GithubApiClient, SignupResult


def sleep(seconds: float) -> None:
    """Sleep for given seconds."""
    time.sleep(seconds)

log = logging.getLogger(__name__)


class HybridSignupFlow:
    """Hybrid signup flow — API-first, browser fallback.

    API mode: ~5s per account (fastest)
    Browser mode: ~30s per account (most reliable)
    """

    def __init__(
        self,
        email_manager: Optional[EmailManager] = None,
        proxy_manager: Optional[ProxyManager] = None,
        mode: str = "auto",  # auto, api, browser
    ):
        self._email = email_manager or EmailManager()
        self._proxy = proxy_manager or ProxyManager()
        self._mode = mode

    def run(
        self,
        username: str,
        password: str,
        email: str,
        proxy: Optional[str] = None,
    ) -> SignupResult:
        """Run signup flow.

        Args:
            username: GitHub username
            password: Account password
            email: Email address for verification
            proxy: Optional proxy URL

        Returns:
            SignupResult with status and cookies
        """
        start = time.time()

        # Get proxy if not provided
        if not proxy:
            proxy = self._proxy.next()

        # Try API-first if mode allows
        if self._mode in ("auto", "api"):
            result = self._try_api(username, password, email, proxy)
            if result.success:
                result.duration_sec = time.time() - start
                return result

            # API failed, try browser if auto mode
            if self._mode == "auto":
                log.info("API failed (%s), trying browser fallback", result.error)
                result = self._try_browser(username, password, email, proxy)

            result.duration_sec = time.time() - start
            return result

        # Browser-only mode
        result = self._try_browser(username, password, email, proxy)
        result.duration_sec = time.time() - start
        return result

    def _try_api(
        self,
        username: str,
        password: str,
        email: str,
        proxy: Optional[str],
    ) -> SignupResult:
        """Try API-only signup."""
        log.info("Trying API signup for %s", username)

        client = GithubApiClient(proxy=proxy)
        try:
            # Warmup
            if not client.warmup():
                return SignupResult(
                    success=False,
                    username=username,
                    password=password,
                    email=email,
                    error="Warmup failed",
                )

            sleep(random.uniform(0.5, 1.5))

            # Get signup page
            page_data = client.get_signup_page()
            if page_data["status_code"] != 200:
                return SignupResult(
                    success=False,
                    username=username,
                    password=password,
                    email=email,
                    error=f"Signup page returned {page_data['status_code']}",
                )

            sleep(random.uniform(0.3, 0.8))

            # Submit signup
            result = client.submit_signup(email, password, username)

            if result.get("is_blocked"):
                return SignupResult(
                    success=False,
                    username=username,
                    password=password,
                    email=email,
                    error="Blocked by GitHub",
                )

            if not result.get("is_verification"):
                return SignupResult(
                    success=False,
                    username=username,
                    password=password,
                    email=email,
                    error="Not redirected to verification",
                )

            # Wait for OTP
            log.info("Waiting for OTP email...")
            otp_code = self._email.poll_otp(
                email,
                sender_contains="github",
                timeout=config.email.otp_timeout,
            )

            sleep(random.uniform(0.5, 1.0))

            # Submit OTP
            otp_result = client.submit_otp(otp_code)

            if otp_result.get("success"):
                log.info("API signup successful for %s", username)
                return SignupResult(
                    success=True,
                    username=username,
                    password=password,
                    email=email,
                    cookies=client.get_session_cookies(),
                )
            else:
                return SignupResult(
                    success=False,
                    username=username,
                    password=password,
                    email=email,
                    error="OTP verification failed",
                )

        except Exception as exc:
            log.warning("API signup failed: %s", exc)
            return SignupResult(
                success=False,
                username=username,
                password=password,
                email=email,
                error=str(exc),
            )
        finally:
            client.close()

    def _try_browser(
        self,
        username: str,
        password: str,
        email: str,
        proxy: Optional[str],
    ) -> SignupResult:
        """Try browser-based signup (fallback)."""
        log.info("Trying browser signup for %s", username)

        from .signup import GithubSignup

        # Select browser driver
        driver_name = config.browser.driver
        if driver_name == "camoufox":
            from src.browser.camoufox import CamoufoxBrowser
            browser = CamoufoxBrowser()
        else:
            from src.browser.patchright import PatchrightBrowser
            browser = PatchrightBrowser()

        try:
            ctx = browser.launch(
                headless=config.browser.headless,
                proxy=proxy,
            )
            page = ctx.new_page()

            signup = GithubSignup(
                page=page,
                email_address=email,
                password=password,
                username=username,
            )

            result = signup.register()

            if result.success:
                # Wait for OTP
                otp_code = self._email.poll_otp(
                    email,
                    sender_contains="github",
                    timeout=config.email.otp_timeout,
                )

                # Enter OTP
                from .verify import enter_otp_code
                enter_otp_code(page, otp_code)

                # Get cookies
                cookies = ctx.cookies()
                cookie_dict = {c["name"]: c["value"] for c in cookies}

                return SignupResult(
                    success=True,
                    username=username,
                    password=password,
                    email=email,
                    cookies=cookie_dict,
                )
            else:
                return SignupResult(
                    success=False,
                    username=username,
                    password=password,
                    email=email,
                    error=result.error,
                )

        except Exception as exc:
            log.warning("Browser signup failed: %s", exc)
            return SignupResult(
                success=False,
                username=username,
                password=password,
                email=email,
                error=str(exc),
            )
        finally:
            try:
                browser.close()
            except Exception:
                pass
