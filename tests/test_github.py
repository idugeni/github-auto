"""Tests for GitHub module."""

from __future__ import annotations

import pytest
from src.github.signup import _gen_username, _gen_password, _is_blocked, _extract_form_errors
from src.github.verify import is_challenge_page, needs_otp


class TestGenUsername:
    def test_prefix(self):
        username = _gen_username()
        assert username.startswith("gh")

    def test_length(self):
        username = _gen_username()
        assert len(username) == 14

    def test_charset(self):
        for _ in range(50):
            username = _gen_username()
            suffix = username[2:]
            assert all(c in "abcdefghijklmnopqrstuvwxyz0123456789" for c in suffix)


class TestGenPassword:
    def test_length(self):
        pw = _gen_password()
        assert len(pw) == 20

    def test_has_digit(self):
        pw = _gen_password()
        assert any(c.isdigit() for c in pw)

    def test_has_lowercase(self):
        pw = _gen_password()
        assert any(c.islower() for c in pw)


class TestIsBlocked:
    def test_normal_page(self):
        assert not _is_blocked("Welcome to GitHub", "GitHub")

    def test_empty_text(self):
        assert _is_blocked("")

    def test_short_text(self):
        assert _is_blocked("Hi")

    def test_datadome(self):
        assert _is_blocked("Access denied by DataDome protection")


class TestExtractFormErrors:
    def test_password_error(self):
        errors = _extract_form_errors("password should be at least 8 characters")
        assert len(errors) == 1
        assert "Password" in errors[0]

    def test_username_taken(self):
        errors = _extract_form_errors("username has already been taken")
        assert len(errors) == 1
        assert "Username" in errors[0]

    def test_no_errors(self):
        errors = _extract_form_errors("Welcome to GitHub! Create your account.")
        assert len(errors) == 0


class TestChallengeDetection:
    def test_challenge_page(self):
        assert is_challenge_page("We detected unusual activity on your account")

    def test_normal_page(self):
        assert not is_challenge_page("Welcome to GitHub")

    def test_otp_needed(self):
        assert needs_otp('<input name="otp" type="text" />')

    def test_no_otp(self):
        assert not needs_otp("<h1>Welcome</h1>")
