"""GitHub provider — ties all modules for GitHub account creation.

Default mode: Hybrid (API-first, browser fallback)
- API mode: ~5s per account (fastest)
- Browser mode: ~30s per account (most reliable)
"""

from __future__ import annotations

import logging
import time
from typing import Optional

from config.settings import config
from src.core.account import Account, AccountStatus
from src.email.manager import EmailManager
from src.proxy.manager import ProxyManager
from src.github.hybrid_flow import HybridSignupFlow, SignupResult

log = logging.getLogger(__name__)


class GithubProvider:
    """High-level GitHub account creation provider.

    Uses hybrid flow: API-first, browser fallback.
    """

    def __init__(
        self,
        email_manager: Optional[EmailManager] = None,
        proxy_manager: Optional[ProxyManager] = None,
        driver: Optional[str] = None,
        headless: Optional[bool] = None,
        debug_screenshots: bool = False,
        mode: str = "auto",  # auto, api, browser
    ):
        self._email = email_manager or EmailManager()
        self._proxy = proxy_manager or ProxyManager()
        self._driver = driver or config.browser.driver
        self._headless = headless if headless is not None else config.browser.headless
        self._debug = debug_screenshots
        self._mode = mode

        # Initialize hybrid flow
        self._flow = HybridSignupFlow(
            email_manager=self._email,
            proxy_manager=self._proxy,
            mode=self._mode,
        )

    def create_account(self, context: Optional[dict] = None) -> Account:
        """Create a single GitHub account.

        Main entry point for pipeline worker.
        """
        index = (context or {}).get("index", 0)
        attempt = (context or {}).get("attempt", 0)

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

        # Run hybrid signup flow
        start = time.time()
        result: SignupResult = self._flow.run(
            username=username,
            password=password,
            email=email_address,
        )

        if result.success:
            account = Account(
                username=result.username,
                password=result.password,
                email=result.email,
                status=AccountStatus.CREATED,
                provider="github",
                proxy=self._proxy.next() or "",
            )
            account.metadata["cookies"] = result.cookies
            account.mark_created()

            # Cleanup email
            try:
                self._email.delete_inbox(email_address, inbox.token)
            except Exception:
                pass

            log.info(
                "[%d] Account created: %s (%.1fs)",
                index, result.username, time.time() - start,
            )
            return account
        else:
            return Account(
                username=username,
                password=password,
                email=email_address,
                status=AccountStatus.FAILED,
                error=result.error,
                proxy=self._proxy.next() or "",
            )
