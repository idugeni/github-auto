"""Abstract CAPTCHA solver interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from playwright.sync_api import Page


class CaptchaSolver(ABC):
    """Base class for CAPTCHA solvers."""

    @abstractmethod
    def solve(self, page: Page, url: Optional[str] = None) -> Optional[str]:
        """Solve CAPTCHA on page. Returns token or None."""
