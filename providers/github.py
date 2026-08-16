"""GitHub provider — undetected-chromedriver approach.

Single session flow:
1. Start browser (uc + xvfb)
2. Warmup homepage (6s)
3. Handle DataDome if needed
4. Signup (8s wait)
5. Email verification
6. Save session
"""

from __future__ import annotations

import logging
import random
import time
from typing import Optional

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from config.settings import config
from src.core.account import Account, AccountStatus
from src.email.manager import EmailManager
from src.proxy.manager import ProxyManager

log = logging.getLogger(__name__)

GITHUB_HOME = "https://github.com/"
GITHUB_SIGNUP = "https://github.com/signup"


class GithubProvider:
    """GitHub account creation with undetected-chromedriver."""

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

        # Start browser
        from src.browser.session import SessionManager
        from src.browser.datadome import DataDomeBypass

        session = SessionManager()
        datadome = DataDomeBypass()

        try:
            proxy = self._proxy.next()
            driver = session.start(headless=False, proxy=proxy)

            # Warmup — 6 seconds on homepage
            log.info("[%d] Warmup homepage...", index)
            driver.get(GITHUB_HOME)
            time.sleep(6)

            # Check for DataDome
            if datadome.is_driver_blocked(driver):
                log.info("[%d] DataDome detected", index)
                if not datadome.wait_for_solve_driver(driver, timeout=60):
                    return Account(
                        username=username, password=password, email=email_address,
                        status=AccountStatus.FAILED, error="DataDome timeout",
                    )

            # Signup page — 8 seconds wait
            log.info("[%d] Signup page...", index)
            driver.get(GITHUB_SIGNUP)
            time.sleep(8)

            # Check for DataDome again
            if datadome.is_driver_blocked(driver):
                if not datadome.wait_for_solve_driver(driver, timeout=60):
                    return Account(
                        username=username, password=password, email=email_address,
                        status=AccountStatus.FAILED, error="DataDome timeout",
                    )

            # Wait for email field
            try:
                WebDriverWait(driver, 30).until(
                    EC.presence_of_element_located((By.ID, "email"))
                )
            except Exception:
                pass

            # Fill form
            log.info("[%d] Filling form...", index)
            self._fill_form(driver, email_address, password, username)
            time.sleep(random.uniform(1, 2))

            # Submit
            self._click_submit(driver)
            time.sleep(5)

            # Check for errors
            body = driver.page_source.lower()
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
                WebDriverWait(driver, 30).until(
                    lambda d: "/account_verifications" in (d.current_url or "")
                )
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
            self._enter_code(driver, otp_code)
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

    def _fill_form(self, driver, email: str, password: str, username: str) -> None:
        """Fill signup form."""
        for el_id, value in [("email", email), ("password", password), ("login", username)]:
            try:
                el = driver.find_element(By.ID, el_id)
                el.click()
                time.sleep(random.uniform(0.3, 0.8))
                el.clear()
                for char in value:
                    el.send_keys(char)
                    time.sleep(random.uniform(0.02, 0.05))
                time.sleep(random.uniform(0.4, 0.9))
            except Exception:
                pass

        # Uncheck consent
        for checkbox_id in ["user_signup[copilot_opt_in]", "user_signup[marketing_consent]"]:
            try:
                cb = driver.find_element(By.ID, checkbox_id)
                if cb.is_selected():
                    cb.click()
            except Exception:
                pass

    def _click_submit(self, driver) -> None:
        """Click Create account button."""
        try:
            buttons = driver.find_elements(By.TAG_NAME, "button")
            for b in buttons:
                if "create account" in (b.text or "").lower():
                    b.click()
                    return
        except Exception:
            pass

    def _enter_code(self, driver, code: str) -> None:
        """Enter OTP code."""
        try:
            # Individual digit inputs
            single_inputs = [
                i for i in driver.find_elements(By.TAG_NAME, "input")
                if i.is_displayed() and (i.get_attribute("maxlength") or "") == "1"
            ]
            if len(single_inputs) >= len(code):
                for i, digit in enumerate(code):
                    single_inputs[i].click()
                    single_inputs[i].send_keys(digit)
                    time.sleep(0.15)
            else:
                # Single input
                inputs = [i for i in driver.find_elements(By.TAG_NAME, "input") if i.is_displayed()]
                if inputs:
                    inputs[0].click()
                    for digit in code:
                        inputs[0].send_keys(digit)
                        time.sleep(0.15)

            time.sleep(0.5)

            # Click continue
            for b in driver.find_elements(By.TAG_NAME, "button"):
                if "continue" in (b.text or "").lower():
                    b.click()
                    return
        except Exception:
            pass
