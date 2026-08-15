"""Tests for browser module."""

from __future__ import annotations

import pytest
from src.browser.human import (
    rand,
    get_recent_chrome_user_agent,
    _pick_random,
)
from src.browser.stealth import get_stealth_script


class TestHumanBehavior:
    def test_rand_range(self):
        for _ in range(100):
            val = rand(5, 10)
            assert 5 <= val < 10

    def test_user_agent_format(self):
        ua = get_recent_chrome_user_agent()
        assert "Mozilla/5.0" in ua
        assert "Chrome/" in ua
        assert "Safari/537.36" in ua

    def test_pick_random(self):
        items = ["a", "b", "c"]
        result = _pick_random(items)
        assert result in items


class TestStealth:
    def test_stealth_script_contains_key_overrides(self):
        script = get_stealth_script("US")
        assert "navigator.webdriver" in script
        assert "navigator.plugins" in script
        assert "WebGLRenderingContext" in script
        assert "HTMLCanvasElement" in script
        assert "canvas_noise" in script.lower() or "toDataURL" in script

    def test_stealth_script_country_languages(self):
        script = get_stealth_script("ID")
        assert "id-ID" in script
