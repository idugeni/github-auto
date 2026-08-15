"""Tests for email module."""

from __future__ import annotations

import pytest
from src.email.supabase import SupabaseEmailProvider
from src.email.base import Inbox


class TestSupabaseOTPExtraction:
    """Test OTP extraction patterns."""

    def test_keyword_before_digits(self):
        code = SupabaseEmailProvider.extract_tp(
            "Verify your account",
            "Your OTP code is 123456. Use it to verify.",
        )
        assert code == "123456"

    def test_digits_before_keyword(self):
        code = SupabaseEmailProvider.extract_otp(
            "GitHub Launch Code",
            "Enter the code below: 87654321 to continue.",
        )
        assert code == "87654321"

    def test_fallback_any_digits(self):
        code = SupabaseEmailProvider.extract_otp(
            "Subject",
            "Please use 998877 for verification.",
        )
        assert code in ("998877", "99887")

    def test_year_filtering(self):
        """Year-like codes should be skipped."""
        code = SupabaseEmailProvider.extract_otp(
            "Subject",
            "Founded in 2024, your code is 556677.",
        )
        assert code == "556677"

    def test_no_code_returns_none(self):
        code = SupabaseEmailProvider.extract_otp(
            "Subject",
            "No verification code here.",
        )
        assert code is None


class TestInbox:
    def test_inbox_creation(self):
        inbox = Inbox(address="test@example.com", token="abc123")
        assert inbox.address == "test@example.com"
        assert inbox.token == "abc123"
