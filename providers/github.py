"""GitHub provider — patchright + xvfb approach.

Single session flow:
1. Start browser (patchright + xvfb)
2. Warmup homepage
3. Handle DataDome if needed
4. Signup
5. Email verification
6. Save session
"""

from __future__ import annotations

import logging
import random
import time
from typing import Optional

from config.settings import config
from src.core.account import Account, AccountStatus
from src.email.manager import EmailManager
from src.proxy.manager import ProxyManager

log = logging.getLogger(__name__)


class GithubProvider:
    """GitHub account creation with patchright browser."""

    def __init__(
        self,
        email_manager: Optional[EmailManager] = None,
        proxy_manager: Optional[ProxyManager] = None,
    ):
        self._email = email_manager or EmailManager()
        self._proxy = proxy_manager or ProxyManager()

    def create_account(self, context: Optional[dict] = None) -> Account:
        """Create a single GitHub account."""
        index = (context or {}).get("index", 0)
        start = time.time()

        # Generate credentials
        from src.github.signup import _gen_username, _gen_password
        username = _gen_username()
        password = _gen_password()

        # Create temp email
        log.info("[%d] Creating email for %s", index, username)
        try:
            inbox = self._email.create_inbox(username)
            email_address = inbox.address
            log.info("[%d] Email: %s", index, email_address)
        except Exception as exc:
            return Account(
                username=username, password=password, email="",
                status=AccountStatus.FAILED, error=str(exc),
            )

        # Start browser session
        from src.browser.session import SessionManager
        from src.browser.datadome import DataDomeBypass
        from src.browser.stealth import apply_stealth

        session = SessionManager()
        datadome = DataDomeBypass()

        try:
            proxy = self._proxy.next()
            page = session.start(headless=False, proxy=proxy)
            ctx = session.get_context()
            apply_stealth(page)

            # Warmup — 6 seconds on homepage (key for DataDome)
            log.info("[%d] Warmup homepage...", index)
            page.goto(GITHUB_HOME, wait_until="networkidle")
            time.sleep(6)  # Critical: 6s warmup per qoderush

            # DataDome check
            if datadome.is_challenge(page):
                log.info("[%d] DataDome detected", index)
                if not datadome.wait_for_solve(page, timeout=60):
                    return Account(
                        username=username, password=password, email=email_address,
                        status=AccountStatus.FAILED, error="DataDome timeout",
                    )

            # Signup page — 8 seconds wait (key for DataDome)
            log.info("[%d] Signup page...", index)
            page.goto(GITHUB_SIGNUP, wait_until="networkidle")
            time.sleep(8)  # Critical: 8s wait per qoderush

            # DataDome check again
            if datadome.is_challenge(page):
                if not datadome.wait_for_solve(page, timeout=60):
                    return Account(
                        username=username, password=password, email=email_address,
                        status=AccountStatus.FAILED, error="DataDome timeout",
                    )

            # Wait for email field
            try:
                page.wait_for_selector("#email", timeout=30_000)
            except Exception:
                pass

            # Fill form
            log.info("[%d] Filling form...", index)
            self._fill_form(page, email_address, password, username)
            time.sleep(random.uniform(1, 2))

            # Submit
            self._click_submit(page)
            time.sleep(5)

            # Check for errors
            body = page.inner_text("body")[:500].lower()
            if "already in use" in body:
                return Account(
                    username=username, password=password, email=email_address,
                    status=AccountStatus.FAILED, error="Username taken",
                )
            if "access is temporarily restricted" in body:
                return Account(
                    username=username, password=password, email=email_address,
                    status=AccountStatus.FAILED, error="Blocked",
                )

            # Wait for verification page
            log.info("[%d] Waiting for verification...", index)
            try:
                page.wait_for_url("**/account_verifications**", timeout=30_000)
            except Exception:
                pass

            # Get OTP
            log.info("[%d] Waiting for OTP...", index)
            otp_code = self._email.poll_otp(
                email_address, "github", config.email.otp_timeout
            )
            log.info("[%d] OTP: %s...", index, otp_code[:3])

            # Enter OTP
            time.sleep(random.uniform(0.5, 1.0))
            self._enter_otp(page, otp_code)
            time.sleep(3)

            # Save session
            session.save_session()

            # Cleanup
            try:
                self._email.delete_inbox(email_address, inbox.token)
            except Exception:
                pass

            account = Account(
                username=username, password=password, email=email_address,
                status=AccountStatus.CREATED, provider="github", proxy=proxy or "",
            )
            account.mark_created()
            log.info("[%d] Created: %s (%.1fs)", index, username, time.time() - start)
            return account

        except Exception as exc:
            log.warning("[%d] Failed: %s", index, exc)
            return Account(
                username=username, password=password, email=email_address,
                status=AccountStatus.FAILED, error=str(exc),
            )
        finally:
            session.close()

    def _fill_form(self, page, email: str, password: str, username: str) -> None:
        """Fill signup form."""
        selectors = {"email": "#email", "password": "#password", "login": "#login"}
        for field, selector in selectors.items():
            value = {"email": email, "password": password, "login": username}[field]
            try:
                el = page.locator(selector)
                if el.count() > 0:
                    el.click()
                    el.type(value, delay=random.randint(30, 80))
                    time.sleep(random.uniform(0.3, 0.8))
            except Exception:
                pass

        # Uncheck consent
        for sel in ["#user_signup_copilot_opt_in", "#user_signup_marketing_consent"]:
            try:
                el = page.locator(sel)
                if el.count() > 0 and el.is_checked():
                    el.uncheck()
            except Exception:
                pass

    def _click_submit(self, page) -> None:
        """Click Create account button."""
        try:
            buttons = page.locator("button")
            for i in range(buttons.count()):
                btn = buttons.nth(i)
                if "create account" in btn.inner_text().lower():
                    btn.click()
                    return
        except Exception:
            pass

    def _enter_otp(self, page, code: str) -> None:
        """Enter OTP code."""
        try:
            # Individual digit inputs
            inputs = page.locator("input[maxlength='1']")
            if inputs.count() >= len(code):
                for i, digit in enumerate(code):
                    inputs.nth(i).type(digit, delay=50)
            else:
                # Single input
                page.locator("input").first.fill(code)

            # Click continue
            buttons = page.locator("button")
            for i in range(buttons.count()):
                btn = buttons.nth(i)
                text = btn.inner_text().lower()
                if any(kw in text for kw in ["continue", "submit", "verify"]):
                    btn.click()
                    break
        except Exception:
            pass


GITHUB_HOME = "https://github.com/"
GITHUB_SIGNUP = "https://github.com/signup"
