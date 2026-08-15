"""Email manager — provider selection with fallback chain.

Primary provider: LewatTok (lewattok.web.id)
Fallback: Supabase
"""

from __future__ import annotations

import logging
from typing import Optional

from config.settings import config
from .base import EmailProvider, Inbox

log = logging.getLogger(__name__)

# Provider priority order (LewatTok first)
PROVIDER_PRIORITY = ["lewattok", "supabase"]


def create_provider(name: Optional[str] = None) -> EmailProvider:
    """Create an email provider by name."""
    provider_name = name or config.email.provider

    providers = {
        "lewattok": _create_lewattok,
        "supabase": _create_supabase,
    }

    factory = providers.get(provider_name)
    if factory:
        return factory()

    log.warning("Unknown provider '%s', defaulting to LewatTok", provider_name)
    return _create_lewattok()


def _create_lewattok() -> EmailProvider:
    from .lewattok import LewatTokClient
    return LewatTokClient(api_key=config.email.lewattok_api_key)


def _create_supabase() -> EmailProvider:
    from .supabase import SupabaseEmailProvider
    return SupabaseEmailProvider(
        supabase_url=config.email.supabase_url,
        publishable_key=config.email.supabase_publishable_key,
    )


def _is_provider_configured(name: str) -> bool:
    """Check if a provider has required config."""
    checks = {
        "lewattok": lambda: bool(config.email.lewattok_api_key),
        "supabase": lambda: bool(config.email.supabase_url and config.email.supabase_publishable_key),
    }
    return checks.get(name, lambda: False)()


class EmailManager:
    """Manages email operations with automatic provider fallback.

    Primary: LewatTok
    Fallback: Supabase
    """

    def __init__(self, primary: Optional[str] = None):
        self._primary_name = primary or config.email.provider
        self._primary = create_provider(self._primary_name)
        self._fallback_chain: list[tuple[str, EmailProvider]] = []

        # Build fallback chain (exclude primary)
        for name in PROVIDER_PRIORITY:
            if name == self._primary_name:
                continue
            try:
                if _is_provider_configured(name):
                    provider = create_provider(name)
                    self._fallback_chain.append((name, provider))
                    log.debug("Added fallback provider: %s", name)
            except Exception as exc:
                log.debug("Failed to init fallback %s: %s", name, exc)

        log.info(
            "Email manager: primary=%s, fallbacks=%s",
            self._primary_name,
            [name for name, _ in self._fallback_chain],
        )

    def create_inbox(self, username: str, domain: Optional[str] = None) -> Inbox:
        """Create inbox with fallback on failure."""
        # Try primary
        try:
            inbox = self._primary.create_inbox(username, domain)
            log.info("Inbox created via %s: %s", self._primary_name, inbox.address)
            return inbox
        except Exception as exc:
            log.warning("Primary (%s) inbox failed: %s", self._primary_name, exc)

        # Try fallbacks
        for name, provider in self._fallback_chain:
            try:
                inbox = provider.create_inbox(username, domain)
                log.info("Inbox created via fallback %s: %s", name, inbox.address)
                return inbox
            except Exception as exc:
                log.warning("Fallback %s inbox failed: %s", name, exc)

        raise RuntimeError("All email providers failed")

    def poll_otp(
        self,
        address: str,
        sender_contains: Optional[str] = None,
        timeout: int = 120,
    ) -> str:
        """Poll OTP with fallback on failure."""
        # Try primary
        try:
            code = self._primary.poll_otp(address, sender_contains, timeout)
            log.info("OTP received via %s", self._primary_name)
            return code
        except TimeoutError:
            log.warning("Primary (%s) OTP timeout", self._primary_name)
        except Exception as exc:
            log.warning("Primary (%s) OTP failed: %s", self._primary_name, exc)

        # Try fallbacks (with shorter timeout)
        fallback_timeout = min(timeout, 30)
        for name, provider in self._fallback_chain:
            try:
                code = provider.poll_otp(address, sender_contains, fallback_timeout)
                log.info("OTP received via fallback %s", name)
                return code
            except (TimeoutError, Exception) as exc:
                log.debug("Fallback %s OTP failed: %s", name, exc)

        raise TimeoutError(f"All email providers failed for OTP: {address}")

    def delete_inbox(self, address: str, token: str = "") -> None:
        """Delete inbox (best effort)."""
        try:
            self._primary.delete_inbox(address, token)
        except Exception as exc:
            log.debug("Delete inbox failed: %s", exc)

    @property
    def primary(self) -> str:
        """Primary provider name."""
        return self._primary_name

    @property
    def fallbacks(self) -> list[str]:
        """Available fallback provider names."""
        return [name for name, _ in self._fallback_chain]
