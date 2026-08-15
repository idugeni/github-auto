"""GitHub provider — ties all modules for GitHub account creation."""

from __future__ import annotations

import logging
import time
from typing import Optional

from config.settings import config
from src.core.account import Account, AccountStatus
from src.email.manager import EmailManager
from src.proxy.manager import ProxyManager
from src.github.signup import GithubSignup, SignupResult
from src.github.verify import (
    wait_for_otp_from_email,
    enter_otp_code,
    handle_device_verification,
)
from src.github.session import save_cookies, save_session

log = logging.getLogger(__name__)


def _create_browser(driver: Optional[str] = None):
    """Create browser driver by name."""
    name = driver or config.browser.driver
    if name == "camoufox":
        from src.browser.camoufox import CamoufoxBrowser
        return CamoufoxBrowser()
    elif name == "patchright":
        from src.browser.patchright import PatchrightBrowser
        return PatchrightBrowser()
    else:
        log.warning("Unknown driver '%s', defaulting to camoufox", name)
        from src.browser.camoufox import CamoufoxBrowser
        return CamoufoxBrowser()


class GithubProvider:
    """High-level GitHub account creation provider."""

    def __init__(
        self,
        email_manager: Optional[EmailManager] = None,
        proxy_manager: Optional[ProxyManager] = None,
        driver: Optional[str] = None,
        headless: Optional[bool] = None,
        debug_screenshots: bool = False,
    ):
        self._email = email_manager or EmailManager()
        self._proxy = proxy_manager or ProxyManager()
        self._driver_name = driver
        self._headless = headless if headless is not None else config.browser.headless
        self._debug = debug_screenshots

    def create_account(self, context: Optional[dict] = None) -> Account:
        """Create a single GitHub account. Main entry point for pipeline worker."""
        index = (context or {}).get("index", 0)
        attempt = (context or {}).get("attempt", 0)

        browser = _create_browser(self._driver_name)
        proxy_url = self._proxy.next()

        try:
            return self._create_one(browser, proxy_url, index, attempt)
        finally:
            browser.close()

    def _create_one(
        self,
        browser,
        proxy_url: Optional[str],
        index: int,
        attempt: int,
    ) -> Account:
        """Internal: create one account with browser."""
        start = time.time()

        # Create temp email
        username = f"gh_{index}_{attempt}_{int(time.time())}"
        log.info("[%d] Creating email inbox for %s", index, username)
        inbox = self._email.create_inbox(username)
        email_address = inbox.address
        log.info("[%d] Email: %s", index, email_address)

        # Launch browser
        ctx = browser.launch(
            headless=self._headless,
            proxy=proxy_url,
        )
        page = ctx.new_page()

        try:
            # Run signup
            signup = GithubSignup(
                page=page,
                email_address=email_address,
                debug_screenshots=self._debug,
            )
            result: SignupResult = signup.register()

            if not result.success:
                return Account(
                    username=result.username,
                    password=result.password,
                    email=result.email,
                    status=AccountStatus.FAILED,
                    error=result.error,
                    proxy=proxy_url or "",
                )

            log.info("[%d] Signup complete, waiting for OTP...", index)

            # Wait for OTP email
            try:
                otp_code = wait_for_otp_from_email(
                    self._email, email_address, "github", config.email.otp_timeout
                )
                log.info("[%d] OTP received: %s...", index, otp_code[:3])

                # Enter OTP
                enter_otp_code(page, otp_code)
                time.sleep(3)

                log.info("[%d] OTP verified", index)

            except TimeoutError:
                log.warning("[%d] OTP timeout, account may need manual verification", index)
                return Account(
                    username=result.username,
                    password=result.password,
                    email=result.email,
                    status=AccountStatus.FAILED,
                    error="OTP timeout",
                    proxy=proxy_url or "",
                )

            # Handle device verification if needed
            page_text = page.inner_text("body")
            if "unusual activity" in page_text.lower() or "verification" in page_text.lower():
                log.info("[%d] Device verification detected, handling...", index)
                handle_device_verification(page, self._email, email_address)

            # Save cookies and session
            save_cookies(ctx, f"data/sessions/{result.username}_cookies.json")
            save_session(page, result.username)

            # Cleanup email inbox
            try:
                self._email.delete_inbox(email_address, inbox.token)
            except Exception:
                pass

            account = Account(
                username=result.username,
                password=result.password,
                email=result.email,
                email_password=result.password,
                status=AccountStatus.CREATED,
                provider="github",
                proxy=proxy_url or "",
            )
            account.mark_created()

            log.info(
                "[%d] Account created: %s (%.1fs)",
                index, result.username, time.time() - start,
            )
            return account

        except Exception as exc:
            log.warning("[%d] Account creation failed: %s", index, exc)
            return Account(
                username=f"failed_{index}",
                password="",
                email=email_address,
                status=AccountStatus.FAILED,
                error=str(exc),
                proxy=proxy_url or "",
            )
        finally:
            try:
                page.close()
                ctx.close()
            except Exception:
                pass
