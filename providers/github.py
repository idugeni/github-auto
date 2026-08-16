"""GitHub provider — pure HTTP approach, no browser.

All operations via HTTP requests with:
- TLS fingerprint impersonation
- Cookie persistence
- Custom CAPTCHA solving
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
from src.github.client import GithubClient

log = logging.getLogger(__name__)


class GithubProvider:
    """High-level GitHub account creation provider.

    Pure HTTP approach — no browser required.
    """

    def __init__(
        self,
        email_manager: Optional[EmailManager] = None,
        proxy_manager: Optional[ProxyManager] = None,
        headless: Optional[bool] = None,
    ):
        self._email = email_manager or EmailManager()
        self._proxy = proxy_manager or ProxyManager()

    def create_account(self, context: Optional[dict] = None) -> Account:
        """Create a single GitHub account via HTTP."""
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

        # Create HTTP client with proxy
        proxy = self._proxy.next()
        client = GithubClient(proxy=proxy)

        try:
            # Step 1: Warmup
            log.info("[%d] Warming up session...", index)
            if not client.warmup():
                return Account(
                    username=username,
                    password=password,
                    email=email_address,
                    status=AccountStatus.FAILED,
                    error="Warmup failed",
                )

            client._human_delay(1000, 2000)

            # Step 2: Get signup page
            log.info("[%d] Getting signup page...", index)
            result = client.get_signup_page()
            if not result.success:
                return Account(
                    username=username,
                    password=password,
                    email=email_address,
                    status=AccountStatus.FAILED,
                    error=result.error,
                )

            client._human_delay(500, 1000)

            # Step 3: Submit signup
            log.info("[%d] Submitting signup...", index)
            result = client.submit_signup(email_address, password, username)

            if result.data.get("is_blocked"):
                return Account(
                    username=username,
                    password=password,
                    email=email_address,
                    status=AccountStatus.FAILED,
                    error="Blocked by GitHub",
                )

            if not result.success:
                return Account(
                    username=username,
                    password=password,
                    email=email_address,
                    status=AccountStatus.FAILED,
                    error=result.error or "Signup failed",
                )

            # Step 4: Wait for OTP
            log.info("[%d] Waiting for OTP...", index)
            otp_code = self._email.poll_otp(
                email_address,
                sender_contains="github",
                timeout=config.email.otp_timeout,
            )
            log.info("[%d] OTP received: %s...", index, otp_code[:3])

            # Step 5: Submit OTP
            client._human_delay(500, 1000)
            result = client.submit_otp(otp_code)

            if result.success:
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
            else:
                return Account(
                    username=username,
                    password=password,
                    email=email_address,
                    status=AccountStatus.FAILED,
                    error=result.error or "OTP verification failed",
                )

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
            client.close()
