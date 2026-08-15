"""GitHub signup flow (ported from qoderush/register.py)."""

from __future__ import annotations

import logging
import random
import string
import time
from dataclasses import dataclass
from typing import Optional

from playwright.sync_api import Page

from config.settings import config
from src.browser.human import (
    type_human,
    random_page_interaction,
)

log = logging.getLogger(__name__)

GITHUB_SIGNUP = "https://github.com/signup"
GITHUB_HOME = "https://github.com/"
BLOCKED_MARKERS = ("access is temporarily restricted", "temporarily restricted", "datadome")


def _gen_username() -> str:
    """Generate random GitHub username."""
    prefix = config.registration.username_prefix
    length = config.registration.username_length - len(prefix)
    chars = string.ascii_lowercase + string.digits
    suffix = "".join(random.choices(chars, k=length))
    return prefix + suffix


def _gen_password() -> str:
    """Generate random password meeting GitHub requirements."""
    length = config.registration.password_length
    chars = string.ascii_letters + string.digits
    pw = "".join(random.choices(chars, k=length - 2))
    # Ensure at least one digit and one lowercase
    pw += random.choice(string.digits)
    pw += random.choice(string.ascii_lowercase)
    return pw


def _is_blocked(page_text: str, title: str = "") -> bool:
    """Check if GitHub is blocking the request."""
    if not page_text or len(page_text) < 50:
        return True
    combined = (title + page_text).lower()
    return any(marker in combined for marker in BLOCKED_MARKERS)


def _extract_form_errors(page_text: str) -> list[str]:
    """Extract form validation errors from page text."""
    errors = []
    lines = page_text.lower().split("\n")
    for line in lines:
        if "password should be at least" in line or "be at least" in line:
            errors.append(f"Password: {line.strip()}")
        elif "username may only contain" in line:
            errors.append(f"Username format: {line.strip()}")
        elif "already in use" in line or "username has already been taken" in line:
            errors.append(f"Username taken: {line.strip()}")
        elif "email is invalid" in line:
            errors.append(f"Email: {line.strip()}")
        elif "there were problems" in line:
            errors.append(f"Form error: {line.strip()}")
    return errors


@dataclass
class SignupResult:
    success: bool = False
    username: str = ""
    password: str = ""
    email: str = ""
    error: str = ""
    duration_sec: float = 0.0


class GithubSignup:
    """GitHub account signup via browser automation."""

    def __init__(
        self,
        page: Page,
        email_address: str,
        password: Optional[str] = None,
        username: Optional[str] = None,
        debug_screenshots: bool = False,
    ):
        self._page = page
        self._email = email_address
        self._password = password or _gen_password()
        self._username = username or _gen_username()
        self._debug = debug_screenshots

    def _screenshot(self, tag: str) -> None:
        if not self._debug:
            return
        try:
            self._page.screenshot(
                path=f"data/results/screenshots/{tag}_{int(time.time())}.png"
            )
        except Exception:
            pass

    def _fill_signup_form(self) -> None:
        """Fill the GitHub signup form."""
        self._page.wait_for_load_state("domcontentloaded")
        try:
            self._page.wait_for_load_state("networkidle", timeout=20_000)
        except Exception:
            pass

        # Wait for email field
        try:
            self._page.wait_for_selector("#email", timeout=20_000)
        except Exception:
            title = self._page.title()
            text = self._page.inner_text("body")
            if _is_blocked(text, title):
                raise RuntimeError("GitHub is blocking access (DataDome/rate limit)")
            self._screenshot("no_email_field")
            raise RuntimeError("Signup form not found")

        # Fill fields with human-like typing
        type_human(self._page, "#email", self._email)
        time.sleep(random.uniform(0.3, 0.8))

        type_human(self._page, "#password", self._password)
        time.sleep(random.uniform(0.3, 0.8))

        type_human(self._page, "#login", self._username)
        time.sleep(random.uniform(0.5, 1.0))

        # Uncheck marketing consent
        for selector in ["#user_signup_copilot_opt_in", "#user_signup_marketing_consent"]:
            try:
                checkbox = self._page.locator(selector)
                if checkbox.count() > 0 and checkbox.is_checked():
                    checkbox.uncheck()
            except Exception:
                pass

        time.sleep(random.uniform(0.5, 1.0))

    def _click_button_containing(self, text: str) -> bool:
        """Click first button whose text contains the given string."""
        buttons = self._page.locator("button")
        count = buttons.count()
        for i in range(count):
            try:
                btn = buttons.nth(i)
                btn_text = btn.inner_text().lower()
                if text.lower() in btn_text:
                    btn.click()
                    return True
            except Exception:
                continue
        return False

    def _enter_code(self, code: str) -> bool:
        """Enter verification code."""
        try:
            self._page.wait_for_load_state("networkidle", timeout=15_000)
        except Exception:
            pass
        time.sleep(2)

        # Check for individual digit inputs
        single_inputs = self._page.locator("input[maxlength='1']")
        if single_inputs.count() >= len(code):
            for i, digit in enumerate(code):
                single_inputs.nth(i).type(digit, delay=random.uniform(30, 80))
        else:
            first_input = self._page.locator("input").first
            first_input.fill(code)

        time.sleep(0.5)
        return self._click_button_containing("continue")

    def register(self) -> SignupResult:
        """Run the full signup flow."""
        start = time.time()

        try:
            return self._do_register()
        except Exception as exc:
            log.warning("Signup failed for %s: %s", self._username, exc)
            self._screenshot("error")
            return SignupResult(
                success=False,
                username=self._username,
                password=self._password,
                email=self._email,
                error=str(exc),
                duration_sec=time.time() - start,
            )

    def _do_register(self) -> SignupResult:
        start = time.time()

        # Warmup — visit homepage first
        log.info("Warming up: %s", GITHUB_HOME)
        self._page.goto(GITHUB_HOME, wait_until="domcontentloaded")
        try:
            self._page.wait_for_load_state("networkidle", timeout=15_000)
        except Exception:
            pass
        time.sleep(random.uniform(3, 6))
        random_page_interaction(self._page)

        # Navigate to signup
        log.info("Navigating to signup page")
        self._page.goto(GITHUB_SIGNUP, wait_until="domcontentloaded")
        try:
            self._page.wait_for_load_state("networkidle", timeout=20_000)
        except Exception:
            pass

        # Fill form
        self._fill_signup_form()

        # Submit
        if not self._click_button_containing("create account"):
            self._screenshot("no_submit_button")
            return SignupResult(
                success=False,
                username=self._username,
                password=self._password,
                email=self._email,
                error="Submit button not found",
                duration_sec=time.time() - start,
            )

        time.sleep(5)

        # Check for form errors
        page_text = self._page.inner_text("body")
        errors = _extract_form_errors(page_text)
        if errors:
            self._screenshot("form_errors")
            return SignupResult(
                success=False,
                username=self._username,
                password=self._password,
                email=self._email,
                error="; ".join(errors),
                duration_sec=time.time() - start,
            )

        # Wait for verification page
        log.info("Waiting for verification page...")
        try:
            self._page.wait_for_url("**/account_verifications**", timeout=30_000)
        except Exception:
            current = self._page.url
            if "signup" in current:
                self._screenshot("stuck_on_signup")
                return SignupResult(
                    success=False,
                    username=self._username,
                    password=self._password,
                    email=self._email,
                    error="Still on signup page after submit",
                    duration_sec=time.time() - start,
                )

        log.info("Verification page reached: %s", self._page.url)

        return SignupResult(
            success=True,
            username=self._username,
            password=self._password,
            email=self._email,
            duration_sec=time.time() - start,
        )

    @property
    def username(self) -> str:
        return self._username

    @property
    def password(self) -> str:
        return self._password

    @property
    def email(self) -> str:
        return self._email
