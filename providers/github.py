"""GitHub provider — camoufox headless approach.

Uses Camoufox (Firefox-based) with headless mode for:
- Deep anti-fingerprint bypass
- DataDome bypass via real Firefox fingerprint
- No visible browser window
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

GITHUB_HOME = "https://github.com/"
GITHUB_SIGNUP = "https://github.com/signup"


class GithubProvider:
    """GitHub account creation with camoufox headless."""

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

        # Start camoufox headless with sticky proxy
        from src.browser.session import SessionManager

        session = SessionManager()
        session_id = f"signup_{username}"
        proxy = self._proxy.next_sticky(session_id, ttl=600)  # 10 min sticky

        try:
            page = session.start(headless=True, proxy=proxy)

            # Step 1: Warmup homepage
            log.info("[%d] Warmup homepage...", index)
            page.goto(GITHUB_HOME, timeout=30000)
            time.sleep(random.uniform(4, 6))

            # Step 2: Signup page
            log.info("[%d] Signup page...", index)
            page.goto(GITHUB_SIGNUP, timeout=30000)

            # Wait for React to render form
            try:
                page.wait_for_selector("#email", timeout=15000)
                log.info("[%d] Signup form loaded", index)
            except Exception:
                log.warning("[%d] Signup form timeout", index)

            time.sleep(random.uniform(1, 2))

            # Step 3: Fill form
            log.info("[%d] Filling form...", index)
            self._fill_form(page, email_address, password, username)
            time.sleep(random.uniform(1, 2))

            # Step 4: Submit
            self._click_submit(page)
            time.sleep(5)

            # Check for errors
            body = page.content().lower()
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

            # Step 5: Wait for verification page
            log.info("[%d] Waiting for verification...", index)
            try:
                page.wait_for_url("**/account_verifications**", timeout=30000)
            except Exception:
                pass

            # Step 6: Get OTP
            log.info("[%d] Waiting for OTP...", index)
            otp_code = self._email.poll_otp(
                email_address, "github", config.email.otp_timeout,
            )
            log.info("[%d] OTP: %s...", index, otp_code[:3])

            # Step 7: Enter OTP
            time.sleep(random.uniform(0.5, 1.0))
            self._enter_code(page, otp_code)
            time.sleep(3)

            # Save session
            session.save_session()

            # Cleanup email
            try:
                self._email.delete_inbox(email_address, inbox.token)
            except Exception:
                pass

            account = Account(
                username=username, password=password, email=email_address,
                status=AccountStatus.CREATED, provider="github",
                proxy=proxy or "",
            )
            account.mark_created()

            # Mark proxy success
            if proxy:
                self._proxy.mark_success(proxy)

            log.info("[%d] Created: %s (%.1fs)", index, username, time.time() - start)
            return account

        except Exception as exc:
            log.warning("[%d] Failed: %s", index, exc)

            # Mark proxy failed, get replacement for next attempt
            if proxy:
                self._proxy.mark_failed(proxy)

            return Account(
                username=username, password=password, email=email_address,
                status=AccountStatus.FAILED, error=str(exc),
            )
        finally:
            self._proxy.release_sticky(session_id)
            session.close()

    def _fill_form(self, page, email: str, password: str, username: str) -> None:
        """Fill signup form."""
        for el_id, value in [("email", email), ("password", password), ("login", username)]:
            try:
                el = page.locator(f"#{el_id}")
                el.click()
                time.sleep(random.uniform(0.3, 0.8))
                el.fill("")
                el.type(value, delay=random.randint(20, 50))
                time.sleep(random.uniform(0.4, 0.9))
            except Exception:
                pass

        # Uncheck consent
        for checkbox_id in ["user_signup[copilot_opt_in]", "user_signup[marketing_consent]"]:
            try:
                cb = page.locator(f"#{checkbox_id}")
                if cb.is_checked():
                    cb.click()
            except Exception:
                pass

    def _click_submit(self, page) -> None:
        """Click Create account button."""
        try:
            buttons = page.locator("button")
            count = buttons.count()
            for i in range(count):
                btn = buttons.nth(i)
                if "create account" in (btn.inner_text() or "").lower():
                    btn.click()
                    return
        except Exception:
            pass

    def _enter_code(self, page, code: str) -> None:
        """Enter OTP code."""
        try:
            # Individual digit inputs
            single_inputs = page.locator("input[maxlength='1']")
            if single_inputs.count() >= len(code):
                for i, digit in enumerate(code):
                    single_inputs.nth(i).click()
                    single_inputs.nth(i).type(digit, delay=50)
            else:
                # Single input
                inputs = page.locator("input")
                count = inputs.count()
                for i in range(count):
                    inp = inputs.nth(i)
                    if inp.is_visible():
                        inp.click()
                        for digit in code:
                            inp.type(digit, delay=50)
                        break

            time.sleep(0.5)

            # Click continue
            buttons = page.locator("button")
            count = buttons.count()
            for i in range(count):
                btn = buttons.nth(i)
                if "continue" in (btn.inner_text() or "").lower():
                    btn.click()
                    return
        except Exception:
            pass
