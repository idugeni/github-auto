"""GitHub Octocaptcha solver.

Handles GitHub's custom challenge system that appears during:
- Account registration
- Login from new device
- Suspicious activity detection

Challenge types:
1. Email verification (6-digit code)
2. Device verification (6-digit code)
3. Security key/passkey prompt
4. CAPTCHA puzzle (rare, fallback to manual)
"""

from __future__ import annotations

import logging
import re
import time
from typing import Optional

from playwright.sync_api import Page

from .base import CaptchaSolver

log = logging.getLogger(__name__)

CHALLENGE_MARKERS = (
    "unusual activity",
    "verification",
    "octocaptcha",
    "confirm your account",
    "checkpoint",
    "verify your identity",
    "we sent you",
    "check your email",
    "device verification",
    "two-factor",
    "2fa",
)

DEVICE_VERIFICATION_URL_PATTERNS = (
    "/sessions/verified-device",
    "/login/device",
    "/account_verifications",
)


class OctocaptchaSolver(CaptchaSolver):
    """Solve GitHub's octocaptcha challenge system."""

    def __init__(self, timeout: int = 180):
        self._timeout = timeout

    def solve(self, page: Page, url: Optional[str] = None) -> Optional[str]:
        """Detect and handle GitHub challenge.

        Returns:
            "resolved" if challenge handled, None if no challenge detected
        """
        if not self._is_github_challenge(page):
            return None

        log.info("GitHub challenge detected")
        return self._handle_challenge(page)

    def _is_github_challenge(self, page: Page) -> bool:
        """Check if page shows a GitHub challenge."""
        try:
            current_url = page.url.lower()
        except Exception:
            return False

        if "github.com" not in current_url:
            return False

        # Check URL patterns
        for pattern in DEVICE_VERIFICATION_URL_PATTERNS:
            if pattern in current_url:
                return True

        # Check page text
        try:
            text = page.locator("body").inner_text(timeout=2000).lower()
            for marker in CHALLENGE_MARKERS:
                if marker in text:
                    return True
        except Exception:
            pass

        # Check for code input fields
        if self._has_code_input(page):
            return True

        return False

    def _has_code_input(self, page: Page) -> bool:
        """Check for OTP/code input fields."""
        selectors = [
            'input[name="otp"]',
            'input[name="code"]',
            'input[name="verification_code"]',
            'input[maxlength="6"]',
            'input[maxlength="8"]',
        ]
        for sel in selectors:
            try:
                if page.locator(sel).count() > 0:
                    return True
            except Exception:
                continue
        return False

    def _handle_challenge(self, page: Page) -> str:
        """Handle the detected challenge."""
        try:
            text = page.locator("body").inner_text(timeout=2000).lower()
        except Exception:
            text = ""

        # Determine challenge type
        if "device verification" in text or "verify your identity" in text:
            log.info("Device verification challenge")
            return "device_verification"

        if "two-factor" in text or "2fa" in text:
            log.info("Two-factor authentication challenge")
            return "two_factor"

        if "unusual activity" in text or "checkpoint" in text:
            log.info("Unusual activity challenge")
            return "unusual_activity"

        if self._has_code_input(page):
            log.info("Code input challenge (OTP required)")
            return "code_input"

        if "passkey" in text or "security key" in text:
            log.info("Passkey/security key challenge (manual intervention needed)")
            return "passkey_required"

        log.warning("Unknown challenge type")
        return "unknown_challenge"

    def detect_challenge_type(self, page: Page) -> str:
        """Detect the specific type of challenge."""
        return self._handle_challenge(page)

    def has_code_input(self, page: Page) -> bool:
        """Public method to check for code input."""
        return self._has_code_input(page)

    def wait_for_code_input(self, page: Page, timeout: int = 30) -> bool:
        """Wait for code input field to appear."""
        selectors = [
            'input[name="otp"]',
            'input[name="code"]',
            'input[name="verification_code"]',
            'input[maxlength="6"]',
            'input[maxlength="8"]',
        ]
        deadline = time.time() + timeout
        while time.time() < deadline:
            for sel in selectors:
                try:
                    if page.locator(sel).count() > 0:
                        return True
                except Exception:
                    continue
            time.sleep(1)
        return False

    def extract_code_from_text(self, text: str) -> Optional[str]:
        """Extract verification code from text."""
        # Pattern: "code is 123456" or "code: 123456"
        match = re.search(r"code\s*(?:is|:)\s*(\d{6})", text, re.I)
        if match:
            return match.group(1)

        # Pattern: any 6-digit code
        match = re.search(r"\b(\d{6})\b", text)
        if match:
            return match.group(1)

        return None

    def enter_code(self, page: Page, code: str) -> bool:
        """Enter verification code."""
        # Try individual digit inputs first
        single_inputs = page.locator("input[maxlength='1']")
        if single_inputs.count() >= len(code):
            for i, digit in enumerate(code):
                single_inputs.nth(i).type(digit, delay=50)
            return self._click_submit(page)

        # Try single input field
        selectors = [
            'input[name="otp"]',
            'input[name="code"]',
            'input[name="verification_code"]',
        ]
        for sel in selectors:
            try:
                field = page.locator(sel)
                if field.count() > 0:
                    field.first.fill(code)
                    return self._click_submit(page)
            except Exception:
                continue

        # Fallback: first input
        try:
            page.locator("input").first.fill(code)
            return self._click_submit(page)
        except Exception as exc:
            log.warning("Failed to enter code: %s", exc)
            return False

    def _click_submit(self, page: Page) -> bool:
        """Click submit/continue button."""
        submit_texts = ["continue", "submit", "verify", "confirm", "next"]
        buttons = page.locator("button")
        count = buttons.count()
        for i in range(count):
            try:
                btn = buttons.nth(i)
                text = btn.inner_text().lower()
                for keyword in submit_texts:
                    if keyword in text:
                        btn.click()
                        return True
            except Exception:
                continue
        return False

    def solve_with_otp(self, page: Page, otp_code: str) -> bool:
        """Solve challenge with provided OTP code."""
        if not self._is_github_challenge(page):
            log.info("No challenge detected")
            return True

        log.info("Entering OTP code: %s...", otp_code[:3])
        success = self.enter_code(page, otp_code)

        if success:
            time.sleep(3)
            # Verify challenge is resolved
            if not self._is_github_challenge(page):
                log.info("Challenge resolved successfully")
                return True
            log.warning("Challenge may not be resolved")
            return False

        log.warning("Failed to enter OTP code")
        return False
