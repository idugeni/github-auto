"""Email manager — provider selection with fallback chain."""

from __future__ import annotations

import logging
from typing import Optional

from config.settings import config
from .base import EmailProvider, Inbox

log = logging.getLogger(__name__)


def create_provider(name: Optional[str] = None) -> EmailProvider:
    """Create an email provider by name with automatic fallback."""
    provider_name = name or config.email.provider

    if provider_name == "lewattok":
        return _create_lewattok()
    elif provider_name == "supabase":
        return _create_supabase()
    else:
        log.warning("Unknown provider '%s', trying LewatTok first", provider_name)
        return _create_lewattok()


def _create_lewattok() -> EmailProvider:
    from .lewattok import LewatTokClient
    return LewatTokClient(api_key=config.email.lewattok_api_key)


def _create_supabase() -> EmailProvider:
    from .supabase import SupabaseEmailProvider
    return SupabaseEmailProvider(
        supabase_url=config.email.supabase_url,
        anon_key=config.email.supabase_anon_key,
    )


class EmailManager:
    """Manages email operations with automatic provider fallback."""

    def __init__(self, primary: Optional[str] = None):
        self._primary = create_provider(primary)
        self._fallback: Optional[EmailProvider] = None

        # Setup fallback if primary might not work
        if primary == "lewattok" and not config.email.lewattok_api_key:
            log.info("LewatTok has no API key, adding Supabase as fallback")
            try:
                self._fallback = _create_supabase()
            except Exception:
                log.warning("Supabase fallback not available")
        elif primary == "supabase" and not config.email.supabase_url:
            log.info("Supabase not configured, adding LewatTok as fallback")
            try:
                self._fallback = _create_lewattok()
            except Exception:
                log.warning("LewatTok fallback not available")

    def create_inbox(self, username: str, domain: Optional[str] = None) -> Inbox:
        """Create inbox with fallback on failure."""
        try:
            return self._primary.create_inbox(username, domain)
        except Exception as exc:
            if self._fallback:
                log.warning("Primary inbox failed (%s), trying fallback", exc)
                return self._fallback.create_inbox(username, domain)
            raise

    def poll_otp(
        self,
        address: str,
        sender_contains: Optional[str] = None,
        timeout: int = 120,
    ) -> str:
        """Poll OTP with fallback on failure."""
        try:
            return self._primary.poll_otp(address, sender_contains, timeout)
        except TimeoutError:
            if self._fallback:
                log.info("Primary OTP timeout, trying fallback")
                try:
                    return self._fallback.poll_otp(address, sender_contains, timeout)
                except TimeoutError:
                    raise
            raise

    def delete_inbox(self, address: str, token: str = "") -> None:
        """Delete inbox (best effort)."""
        try:
            self._primary.delete_inbox(address, token)
        except Exception as exc:
            log.debug("Delete inbox failed: %s", exc)
