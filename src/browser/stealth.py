"""Anti-detection stealth injection."""

from __future__ import annotations

from playwright.sync_api import Page


def get_stealth_script() -> str:
    """Generate minimal stealth script for patchright."""
    return """
    // webdriver
    Object.defineProperty(navigator, 'webdriver', { get: () => undefined });

    // Chrome runtime
    if (!window.chrome) window.chrome = {};
    if (!window.chrome.runtime) window.chrome.runtime = { connect: function() {}, sendMessage: function() {} };
    """


def apply_stealth(page: Page) -> None:
    """Apply stealth to page."""
    page.add_init_script(get_stealth_script())
