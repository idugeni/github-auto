"""GitHub provider — ties all modules for GitHub account creation.

Uses single session throughout:
1. Start session (patchright + xvfb)
2. Warmup homepage
3. Bypass DataDome
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
    """High-level GitHub account creation provider.

    Single session approach for maximum stealth.
    """

    def __init__(
        self,
        email_manager: Optional[EmailManager] = None,
        proxy_manager: Optional[ProxyManager] = None,
        headless: Optional[bool] = None,
    ):
        self._email = email_manager or EmailManager()
        self._proxy = proxy_manager or ProxyManager()
        self._headless = headless if headless is not None else config.browser.headless

    def create_account(self, context: Optional[dict] = None) -> Account:
        """Create a single GitHub account.

        Uses single browser session throughout.
        """
        index = (context or {}).get("index", 0)
        start = time.time()

        # Generate credentials
        from src.github.signup import _gen_username, _gen_password
        username = _gen_username()
        password = _gen_password()

        # Create temp email
        log.info("[%d] Creating email inbox for %s", index, username)
        try:
            inbox = self._email.create_inbox(username)
            email_address = inbox.address
            log.info("[%d] Email: %s", index, email_address)
        except Exception as exc:
            log.warning("[%d] Email creation failed: %s", index, exc)
            return Account(
                username=username,
                password=password,
                email="",
                status=AccountStatus.FAILED,
                error=f"Email creation failed: {exc}",
            )

        # Run signup in single session
        from src.browser.session import SessionManager
        from src.browser.datadome import DataDomeBypass

        session = SessionManager()
        datadome = DataDomeBypass()

        try:
            # Start session
            proxy = self._proxy.next()
            page = session.start(
                headless=self._headless,
                proxy=proxy,
            )
            context = session.get_context()

            # Load saved DataDome cookies
            datadome.load_cookies(context)

            # Step 1: Warmup homepage
            log.info("[%d] Warming up homepage...", index)
            page.goto("https://github.com/", wait_until="networkidle")
            time.sleep(random.uniform(2, 4))

            # Step 2: Handle DataDome if present
            if datadome.is_challenge(page):
                log.info("[%d] DataDome challenge detected", index)
                if not datadome.solve_challenge(page):
                    return Account(
                        username=username,
                        password=password,
                        email=email_address,
                        status=AccountStatus.FAILED,
                        error="DataDome challenge failed",
                    )

            # Step 3: Navigate to signup
            log.info("[%d] Navigating to signup...", index)
            page.goto("https://github.com/signup", wait_until="networkidle")
            time.sleep(random.uniform(3, 5))

            # Check for DataDome again
            if datadome.is_challenge(page):
                log.info("[%d] DataDome challenge on signup page", index)
                if not datadome.solve_challenge(page):
                    return Account(
                        username=username,
                        password=password,
                        email=email_address,
                        status=AccountStatus.FAILED,
                        error="DataDome challenge on signup failed",
                    )

            # Step 4: Fill signup form
            log.info("[%d] Filling signup form...", index)
            from src.github.signup import GithubSignup
            signup = GithubSignup(
                page=page,
                email_address=email_address,
                password=password,
                username=username,
            )
            result = signup.register()

            if not result.success:
                return Account(
                    username=username,
                    password=password,
                    email=email_address,
                    status=AccountStatus.FAILED,
                    error=result.error,
                )

            # Step 5: Wait for OTP
            log.info("[%d] Waiting for OTP...", index)
            otp_code = self._email.poll_otp(
                email_address,
                sender_contains="github",
                timeout=config.email.otp_timeout,
            )
            log.info("[%d] OTP received: %s...", index, otp_code[:3])

            # Step 6: Enter OTP
            time.sleep(random.uniform(0.5, 1.0))
            from src.github.verify import enter_otp_code
            enter_otp_code(page, otp_code)

            # Step 7: Save session
            session.save_session()
            datadome.save_cookies(context)

            # Create account
            account = Account(
                username=username,
                password=password,
                email=email_address,
                status=AccountStatus.CREATED,
                provider="github",
                proxy=proxy or "",
            )
            account.mark_created()

            # Cleanup email
            try:
                self._email.delete_inbox(email_address, inbox.token)
            except Exception:
                pass

            log.info(
                "[%d] Account created: %s (%.1fs)",
                index, username, time.time() - start,
            )
            return account

        except Exception as exc:
            log.warning("[%d] Account creation failed: %s", index, exc)
            return Account(
                username=username,
                password=password,
                email=email_address,
                status=AccountStatus.FAILED,
                error=str(exc),
            )
        finally:
            session.close()
