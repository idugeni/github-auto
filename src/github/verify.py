"""GitHub email/device verification and OTP entry."""

from __future__ import annotations

import logging
import re
import time
from typing import Optional

from playwright.sync_api import Page

from src.captcha.octocaptcha import OctocaptchaSolver

log = logging.getLogger(__name__)

CHALLENGE_MARKERS = (
    "unusual activity",
    "verification",
    "octocaptcha",
    "confirm your account",
    "checkpoint",
)


def is_challenge_page(page_text: str) -> bool:
    """Check if page looks like a GitHub challenge."""
    lower = page_text.lower()
    return any(marker in lower for marker in CHALLENGE_MARKERS)


def needs_otp(html: str) -> bool:
    """Check if page requires OTP input."""
    lower = html.lower()
    return any(
        kw in lower
        for kw in ("two-factor", "otp", 'name="otp"', "authentication code")
    )


def detect_challenge_type(page: Page) -> str:
    """Detect the specific type of GitHub challenge.

    Returns:
        Challenge type: "device_verification", "two_factor", "unusual_activity",
                       "code_input", "passkey_required", "unknown_challenge", or "none"
    """
    solver = OctocaptchaSolver()
    if not solver._is_github_challenge(page):
        return "none"
    return solver.detect_challenge_type(page)


def enter_otp_code(page: Page, code: str) -> bool:
    """Enter OTP code on verification page."""
    try:
        page.wait_for_load_state("networkidle", timeout=15_000)
    except Exception:
        pass
    time.sleep(2)

    # Detect code input style
    single_inputs = page.locator("input[maxlength='1']")
    if single_inputs.count() >= len(code):
        # Individual digit inputs
        for i, digit in enumerate(code):
            single_inputs.nth(i).type(digit, delay=50)
    else:
        # Single input field
        code_field = _find_code_field(page)
        if code_field:
            code_field.fill(code)
        else:
            # Fallback: try first input
            page.locator("input").first.fill(code)

    time.sleep(0.5)

    # Click continue/submit button
    return _click_submit(page)


def _find_code_field(page: Page) -> Optional[object]:
    """Find the OTP code input field."""
    selectors = [
        'input[name="otp"]',
        'input[name="code"]',
        'input[name="verification_code"]',
        'input[name="app_otp"]',
        'input[name="device_code"]',
        "#otp",
        "#code",
    ]
    for sel in selectors:
        try:
            el = page.locator(sel)
            if el.count() > 0:
                return el.first
        except Exception:
            continue
    return None


def _click_submit(page: Page) -> bool:
    """Click the submit/continue button."""
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


def wait_for_otp_from_email(
    email_manager,
    address: str,
    sender_contains: str = "github",
    timeout: int = 120,
) -> str:
    """Wait for OTP code from email provider."""
    return email_manager.poll_otp(address, sender_contains, timeout)


def handle_device_verification(
    page: Page,
    email_manager,
    email_address: str,
    timeout: int = 180,
) -> bool:
    """Handle GitHub device verification flow.

    Uses OctocaptchaSolver for challenge detection and OTP entry.
    """
    log.info("Handling device verification for %s", email_address)

    solver = OctocaptchaSolver(timeout=timeout)

    # Check if there's a challenge
    if not solver._is_github_challenge(page):
        log.debug("Not a challenge page")
        return True

    # Detect challenge type
    challenge_type = solver.detect_challenge_type(page)
    log.info("Challenge type: %s", challenge_type)

    # Handle based on challenge type
    if challenge_type == "passkey_required":
        log.warning("Passkey/security key challenge - requires manual intervention")
        return False

    if challenge_type in ("device_verification", "two_factor", "unusual_activity", "code_input"):
        # Wait for OTP from email
        try:
            otp_code = wait_for_otp_from_email(
                email_manager, email_address, "github", timeout
            )
            log.info("Got OTP code: %s...", otp_code[:3])

            if solver.solve_with_otp(page, otp_code):
                log.info("Device verification successful")
                return True

            log.warning("OTP entered but challenge may not be resolved")
            return False

        except TimeoutError:
            log.warning("OTP timeout during device verification")
            return False

    log.warning("Unhandled challenge type: %s", challenge_type)
    return False
