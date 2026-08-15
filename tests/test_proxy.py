"""Tests for proxy module."""

from __future__ import annotations

import pytest
from src.proxy.manager import ProxyManager
from src.proxy.detect import ProxyInfo, _calc_factor


class TestProxyParsing:
    def test_parse_simple(self):
        mgr = ProxyManager(static_proxy="http://proxy.example.com:8080")
        proxy = mgr.next()
        assert proxy == "http://proxy.example.com:8080"

    def test_parse_with_auth(self):
        mgr = ProxyManager(static_proxy="socks5://user:pass@proxy.com:1080")
        proxy = mgr.next()
        assert proxy == "socks5://user:pass@proxy.com:1080"

    def test_empty_returns_none(self):
        mgr = ProxyManager()
        assert mgr.next() is None


class TestProxyRotation:
    def test_sticky_same_proxy(self):
        mgr = ProxyManager(
            static_proxy="http://proxy1.com:8080",
            cooldown=0,
        )
        p1 = mgr.next()
        p2 = mgr.next()
        assert p1 == p2

    def test_mark_failed(self):
        mgr = ProxyManager(
            static_proxy="http://proxy1.com:8080",
            cooldown=0,
        )
        url = mgr.next()
        if url:
            mgr.mark_failed(url)
        # Should still return (fail_count < 3)
        assert mgr.next() == url


class TestLatencyFactor:
    def test_fast(self):
        assert _calc_factor(500) == 1.0

    def test_medium(self):
        assert _calc_factor(2000) == 1.5

    def test_slow(self):
        assert _calc_factor(4000) == 2.5


class TestProxyInfo:
    def test_defaults(self):
        info = ProxyInfo()
        assert info.country_code == "US"
        assert info.latency_ms == 0.0
