"""Abstract browser driver interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import Generator, Optional

from playwright.sync_api import BrowserContext, Page


class BrowserDriver(ABC):
    """Base class for browser automation drivers."""

    @abstractmethod
    def launch(
        self,
        headless: bool = False,
        proxy: Optional[str] = None,
        viewport_width: int = 1280,
        viewport_height: int = 720,
    ) -> BrowserContext:
        """Launch browser context."""

    @abstractmethod
    def close(self) -> None:
        """Close browser and clean up resources."""

    @contextmanager
    def session(
        self,
        headless: bool = False,
        proxy: Optional[str] = None,
    ) -> Generator[tuple[BrowserContext, Page], None, None]:
        """Context manager for browser session."""
        ctx = self.launch(headless=headless, proxy=proxy)
        page = ctx.new_page()
        try:
            yield ctx, page
        finally:
            page.close()
            ctx.close()
            self.close()
