"""Anti-detection stealth injection for camoufox."""

from __future__ import annotations

from typing import Any


def apply_stealth(page: Any) -> None:
    """Apply stealth measures to page."""
    page.add_init_script("""
        // Hide webdriver
        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });

        // Chrome runtime
        if (!window.chrome) window.chrome = {};
        if (!window.chrome.runtime) window.chrome.runtime = { connect: function() {}, sendMessage: function() {} };
    """)
