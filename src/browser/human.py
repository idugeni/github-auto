"""Human-like behavior simulation (typing, mouse, scroll)."""

from __future__ import annotations

import random
import time
from typing import Optional

from playwright.sync_api import Page, Locator


def sleep(ms: float) -> None:
    """Sleep for milliseconds."""
    time.sleep(ms / 1000)


def rand(min_val: int, max_val: int) -> int:
    """Random integer in [min, max)."""
    return random.randint(min_val, max_val - 1)


def type_human(page: Page, selector: str, text: str) -> None:
    """Type text character by character with random delays."""
    page.click(selector)
    for char in text:
        page.keyboard.type(char, delay=random.uniform(60, 180))
        sleep(rand(10, 30))


def fill_human(page: Page, locator: Locator, text: str) -> None:
    """Fill input with human-like sequential typing."""
    try:
        locator.click(force=True)
    except Exception:
        locator.focus()
    locator.fill("")
    for char in text:
        locator.press_sequentially(char, delay=random.uniform(20, 50))
        sleep(rand(5, 15))


def human_mouse_move(
    page: Page,
    start_x: Optional[int] = None,
    start_y: Optional[int] = None,
    end_x: Optional[int] = None,
    end_y: Optional[int] = None,
    steps: Optional[int] = None,
) -> None:
    """Simulate human-like mouse movement with easing."""
    sx = start_x or rand(200, 600)
    sy = start_y or rand(200, 400)
    ex = end_x or rand(300, 900)
    ey = end_y or rand(300, 500)
    n = steps or rand(8, 20)

    for i in range(n):
        t = i / n
        # Quadratic ease-in-out
        ease = t * t * (3 - 2 * t)
        x = sx + (ex - sx) * ease + random.uniform(-3, 3)
        y = sy + (ey - sy) * ease + random.uniform(-3, 3)
        page.mouse.move(x, y)
        sleep(rand(5, 20))


def human_scroll(page: Page, times: Optional[int] = None) -> None:
    """Simulate random scrolling."""
    n = times or rand(1, 3)
    for _ in range(n):
        delta = random.randint(-150, 300)
        page.mouse.wheel(0, delta)
        sleep(rand(200, 600))


def random_page_interaction(page: Page) -> None:
    """Random mouse move + scroll."""
    human_mouse_move(page)
    sleep(rand(300, 800))
    human_scroll(page)
    sleep(rand(200, 500))


def get_recent_chrome_user_agent() -> str:
    """Generate a recent Chrome user-agent string."""
    base_major = 126
    months_since = 14  # ~June 2024 + 14 months = Aug 2025
    major = base_major + int(months_since * 1.08)
    build = random.randint(6000, 6999)
    patch = random.randint(0, 149)
    return (
        f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        f"AppleWebKit/537.36 (KHTML, like Gecko) "
        f"Chrome/{major}.0.{build}.{patch} Safari/537.36"
    )
