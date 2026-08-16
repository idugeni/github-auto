"""Anti-detection stealth injection for browsers.

Note: Camoufox handles most fingerprinting internally.
This module adds supplementary anti-detection measures.
"""

from __future__ import annotations

import json
import random
from typing import Optional

from playwright.sync_api import Page

LANGUAGES_BY_COUNTRY = {
    "US": ["en-US", "en"],
    "GB": ["en-GB", "en"],
    "ID": ["id-ID", "id", "en-US", "en"],
    "DE": ["de-DE", "de", "en-US", "en"],
    "FR": ["fr-FR", "fr", "en-US", "en"],
    "JP": ["ja-JP", "ja", "en-US", "en"],
}


def get_stealth_script(country_code: str = "US", user_agent: str = "") -> str:
    """Generate minimal stealth injection script.

    Camoufox handles most fingerprinting. This only adds:
    - webdriver removal
    - Language consistency
    - Chrome runtime (for sites that check)
    """
    languages = LANGUAGES_BY_COUNTRY.get(country_code, ["en-US", "en"])

    return """
    // webdriver
    Object.defineProperty(navigator, 'webdriver', { get: () => undefined });

    // Chrome runtime
    if (!window.chrome) window.chrome = {};
    if (!window.chrome.runtime) window.chrome.runtime = { connect: function() {}, sendMessage: function() {} };

    // Notification permission
    if (typeof Notification !== 'undefined') {
        Object.defineProperty(Notification, 'permission', { get: () => 'default' });
    }
    """


def apply_stealth(page: Page, country_code: str = "US", user_agent: str = "") -> None:
    """Apply stealth script to a Playwright page."""
    script = get_stealth_script(country_code, user_agent)
    page.add_init_script(script)


CHROME_ARGS = [
    "--disable-blink-features=AutomationControlled",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    "--disable-webrtc",
    "--disable-extensions",
    "--disable-infobars",
    "--window-size=1920,1080",
    "--start-maximized",
    "--disable-background-networking",
    "--disable-background-timer-throttling",
    "--disable-backgrounding-occluded-windows",
    "--disable-breakpad",
    "--disable-client-side-phishing-detection",
    "--disable-component-update",
    "--disable-default-apps",
    "--disable-domain-reliability",
    "--disable-hang-monitor",
    "--disable-ipc-flooding-protection",
    "--disable-popup-blocking",
    "--disable-prompt-on-repost",
    "--disable-renderer-backgrounding",
    "--disable-sync",
    "--metrics-recording-only",
    "--no-first-run",
    "--password-store=basic",
    "--use-mock-keychain",
]
