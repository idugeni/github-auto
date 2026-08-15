"""Abstract email provider interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class Inbox:
    address: str
    token: str = ""
    domain: str = ""


class EmailProvider(ABC):
    """Base class for temporary email providers."""

    @abstractmethod
    def create_inbox(self, username: str, domain: Optional[str] = None) -> Inbox:
        """Create a new temporary email inbox."""

    @abstractmethod
    def poll_otp(
        self,
        address: str,
        sender_contains: Optional[str] = None,
        timeout: int = 120,
    ) -> str:
        """Poll for an OTP code. Raises TimeoutError on failure."""

    @abstractmethod
    def delete_inbox(self, address: str, token: str) -> None:
        """Delete an email inbox."""
