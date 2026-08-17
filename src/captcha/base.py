"""Abstract CAPTCHA solver interface — HTTP-based, no browser."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional


class CaptchaSolver(ABC):
    """Base class for CAPTCHA solvers."""

    @abstractmethod
    def solve(self, site_url: str, site_key: str, **kwargs) -> Optional[str]:
        """Solve CAPTCHA via API. Returns token or None."""
