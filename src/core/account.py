"""Account data model."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class AccountStatus(str, Enum):
    PENDING = "pending"
    CREATED = "created"
    VERIFIED = "verified"
    FAILED = "failed"


class Account(BaseModel):
    """GitHub account data model."""

    username: str
    password: str
    email: str
    email_password: str = ""
    status: AccountStatus = AccountStatus.PENDING
    recovery_codes: list[str] = Field(default_factory=list)
    session_cookies: dict = Field(default_factory=dict)
    provider: str = ""
    proxy: str = ""
    error: str = ""
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    verified_at: Optional[str] = None
    metadata: dict = Field(default_factory=dict)

    def mark_created(self) -> None:
        self.status = AccountStatus.CREATED
        self.created_at = datetime.now(timezone.utc).isoformat()

    def mark_verified(self) -> None:
        self.status = AccountStatus.VERIFIED
        self.verified_at = datetime.now(timezone.utc).isoformat()

    def mark_failed(self, error: str) -> None:
        self.status = AccountStatus.FAILED
        self.error = error

    def to_creds_line(self) -> str:
        """Export as pipe-delimited creds line."""
        return f"{self.email}|{self.password}|{self.username}"
