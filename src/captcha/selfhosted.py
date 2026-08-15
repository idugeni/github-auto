"""Self-hosted CAPTCHA solver.

Unified solver that handles multiple CAPTCHA types without external services.
Uses browser automation + local ASR for audio challenges.

Supported:
- reCAPTCHA (audio challenge + Whisper ASR)
- Cloudflare Turnstile (iframe interaction)
- hCaptcha (iframe interaction)
- FunCaptcha/Arkose (iframe interaction)
"""

from __future__ import annotations

import logging
import os
import random
import re
import time
from typing import Any, Optional

from playwright.sync_api import Page

from .base import CaptchaSolver

log = logging.getLogger(__name__)


class SelfHostedSolver(CaptchaSolver):
    """Unified self-hosted CAPTCHA solver.

    Detects CAPTCHA type and routes to appropriate solver.
    No external API dependencies except optional Whisper for audio ASR.
    """

    def __init__(
        self,
        whisper_api_url: Optional[str] = None,
        whisper_api_key: Optional[str] = None,
        timeout: int = 180,
    ):
        self._whisper_url = whisper_api_url or os.getenv(
            "WHISPER_API_URL", "https://api.groq.com/openai/v1"
        )
        self._whisper_key = whisper_api_key or os.getenv("GROQ_API_KEY", "")
        self._timeout = timeout
        self._whisper_client = None

    def _get_whisper_client(self):
        """Lazy-init Whisper client."""
        if self._whisper_client is None and self._whisper_key:
            from openai import OpenAI
            self._whisper_client = OpenAI(
                api_key=self._whisper_key,
                base_url=self._whisper_url,
            )
        return self._whisper_client

    def solve(self, page: Page, url: Optional[str] = None) -> Optional[str]:
        """Detect and solve CAPTCHA on page.

        Returns:
            Solved token or None
        """
        captcha_type = self.detect_type(page, url)
        if captcha_type == "none":
            return None

        log.info("Detected CAPTCHA: %s", captcha_type)

        if captcha_type == "recaptcha":
            return self._solve_recaptcha(page)
        elif captcha_type == "turnstile":
            return self._solve_turnstile(page)
        elif captcha_type == "hcaptcha":
            return self._solve_hcaptcha(page)
        elif captcha_type == "funcaptcha":
            return self._solve_funcaptcha(page)

        return None

    def detect_type(self, page: Page) -> str:
        """Detect CAPTCHA type on page."""
        try:
            html = page.content().lower()
            url = page.url.lower()
        except Exception:
            return "none"

        # reCAPTCHA
        if "recaptcha" in html or "grecaptcha" in html:
            return "recaptcha"

        # Cloudflare Turnstile
        if "turnstile" in html or "challenges.cloudflare.com" in html:
            return "turnstile"

        # hCaptcha
        if "hcaptcha" in html or "hcaptcha.com" in html:
            return "hcaptcha"

        # FunCaptcha/Arkose
        if "funcaptcha" in html or "arkoselabs" in html or "fc-" in html:
            return "funcaptcha"

        # Check iframes
        try:
            iframes = page.frames
            for frame in iframes:
                frame_url = (frame.url or "").lower()
                if "recaptcha" in frame_url:
                    return "recaptcha"
                if "challenges.cloudflare.com" in frame_url:
                    return "turnstile"
                if "hcaptcha.com" in frame_url:
                    return "hcaptcha"
                if "arkoselabs" in frame_url or "funcaptcha" in frame_url:
                    return "funcaptcha"
        except Exception:
            pass

        return "none"

    # ------------------------------------------------------------------ #
    # reCAPTCHA Solver
    # ------------------------------------------------------------------ #

    def _solve_recaptcha(self, page: Page) -> Optional[str]:
        """Solve reCAPTCHA via audio challenge."""
        log.info("Solving reCAPTCHA...")

        # Find reCAPTCHA iframe
        anchor_frame = None
        for frame in page.frames:
            if "recaptcha/anchor" in (frame.url or ""):
                anchor_frame = frame
                break

        if not anchor_frame:
            log.debug("No reCAPTCHA anchor frame")
            return None

        # Check if already solved
        try:
            checked = anchor_frame.locator("#recaptcha-anchor").get_attribute(
                "aria-checked", timeout=2000
            )
            if checked == "true":
                return "already_solved"
        except Exception:
            pass

        # Click checkbox
        try:
            anchor_frame.locator("#recaptcha-anchor").click()
            time.sleep(2)
        except Exception as exc:
            log.debug("Failed to click reCAPTCHA checkbox: %s", exc)
            return None

        # Check if solved instantly
        try:
            checked = anchor_frame.locator("#recaptcha-anchor").get_attribute(
                "aria-checked", timeout=3000
            )
            if checked == "true":
                return "solved_instantly"
        except Exception:
            pass

        # Find challenge frame
        challenge_frame = None
        for frame in page.frames:
            if "recaptcha/bframe" in (frame.url or ""):
                challenge_frame = frame
                break

        if not challenge_frame:
            return None

        # Click audio button
        try:
            audio_btn = challenge_frame.locator("#rc-audiochallenge-instructions-link")
            if audio_btn.count() > 0:
                audio_btn.click()
                time.sleep(1)
        except Exception:
            log.debug("No audio button (may be Enterprise)")
            return None

        # Download and transcribe audio
        for attempt in range(3):
            try:
                audio_link = challenge_frame.locator("#rc-audiochallenge-download-link")
                if audio_link.count() == 0:
                    time.sleep(1.5)
                    continue

                audio_url = audio_link.get_attribute("href")
                if not audio_url:
                    continue

                # Download audio
                import tempfile
                import requests
                resp = requests.get(audio_url, timeout=10)
                audio_path = os.path.join(tempfile.gettempdir(), f"captcha_{int(time.time())}.mp3")
                with open(audio_path, "wb") as f:
                    f.write(resp.content)

                # Transcribe
                text = self._transcribe_audio(audio_path)
                if not text:
                    continue

                cleaned = re.sub(r"[^a-zA-Z0-9\s]", "", text).strip().lower()
                log.info("Transcribed: '%s'", cleaned)

                # Fill answer
                response_input = challenge_frame.locator("#audio-response")
                response_input.fill("")
                response_input.type(cleaned, delay=50)

                # Verify
                challenge_frame.locator("#recaptcha-verify-button").click()
                time.sleep(2)

                # Check result
                try:
                    checked = anchor_frame.locator("#recaptcha-anchor").get_attribute(
                        "aria-checked", timeout=3000
                    )
                    if checked == "true":
                        return "audio_solved"
                except Exception:
                    pass

                # Cleanup
                try:
                    os.unlink(audio_path)
                except Exception:
                    pass

            except Exception as exc:
                log.debug("reCAPTCHA attempt %d failed: %s", attempt + 1, exc)

        return None

    def _transcribe_audio(self, audio_path: str) -> Optional[str]:
        """Transcribe audio file via Whisper."""
        client = self._get_whisper_client()
        if not client:
            log.warning("No Whisper client configured")
            return None

        try:
            with open(audio_path, "rb") as f:
                result = client.audio.transcriptions.create(
                    model="whisper-large-v3-turbo",
                    file=f,
                    language="en",
                )
            return result.text
        except Exception as exc:
            log.warning("Whisper transcription failed: %s", exc)
            return None

    # ------------------------------------------------------------------ #
    # Turnstile Solver
    # ------------------------------------------------------------------ #

    def _solve_turnstile(self, page: Page) -> Optional[str]:
        """Solve Cloudflare Turnstile."""
        log.info("Solving Turnstile...")

        deadline = time.time() + self._timeout

        # Find Turnstile iframe
        iframe = self._find_iframe(page, ["challenges.cloudflare.com", "turnstile"], deadline)
        if not iframe:
            return None

        # Get bounding box
        try:
            box = iframe.bounding_box()
            if not box:
                return None
        except Exception:
            return None

        # Move mouse around to trigger invisible challenge
        for _ in range(30):
            if time.time() > deadline:
                break

            x = box["x"] + random.uniform(0, box["width"])
            y = box["y"] + random.uniform(0, box["height"])
            page.mouse.move(x, y)
            time.sleep(random.uniform(0.1, 0.3))

            token = self._get_turnstile_token(page)
            if token:
                return token

        # Try clicking checkbox
        try:
            frame_page = iframe
            checkbox = frame_page.locator("input[type='checkbox'], .cb-lb")
            if checkbox.count() > 0:
                checkbox.first.click()
                time.sleep(3)
                token = self._get_turnstile_token(page)
                if token:
                    return token
        except Exception:
            pass

        return None

    def _get_turnstile_token(self, page: Page) -> Optional[str]:
        """Extract Turnstile token."""
        try:
            token_input = page.locator("[name='cf-turnstile-response']")
            if token_input.count() > 0:
                token = token_input.first.input_value()
                if token and len(token) > 10:
                    return token
        except Exception:
            pass

        try:
            token = page.evaluate("""
                () => {
                    const input = document.querySelector('[name="cf-turnstile-response"]');
                    if (input && input.value) return input.value;
                    if (window.turnstile) return window.turnstile.getResponse();
                    return null;
                }
            """)
            if token and len(str(token)) > 10:
                return str(token)
        except Exception:
            pass

        return None

    # ------------------------------------------------------------------ #
    # hCaptcha Solver
    # ------------------------------------------------------------------ #

    def _solve_hcaptcha(self, page: Page) -> Optional[str]:
        """Solve hCaptcha via browser automation."""
        log.info("Solving hCaptcha...")

        deadline = time.time() + self._timeout

        # Find hCaptcha iframe
        iframe = self._find_iframe(page, ["hcaptcha.com", "hcaptcha"], deadline)
        if not iframe:
            return None

        # Get bounding box
        try:
            box = iframe.bounding_box()
            if not box:
                return None
        except Exception:
            return None

        # Move mouse to iframe area
        x = box["x"] + box["width"] / 2 + random.uniform(-20, 20)
        y = box["y"] + box["height"] / 2 + random.uniform(-10, 10)
        self._human_move(page, x, y)

        # Try to click checkbox inside iframe
        try:
            frame_page = iframe
            checkbox = frame_page.locator("#checkbox, .checkbox, [role='checkbox']")
            if checkbox.count() > 0:
                checkbox.first.click()
                time.sleep(3)

                # Check for token
                token = self._get_hcaptcha_token(page)
                if token:
                    return token

                # May need to solve image challenge
                log.info("hCaptcha checkbox clicked, may need image challenge")
                return None
        except Exception as exc:
            log.debug("hCaptcha click failed: %s", exc)

        return None

    def _get_hcaptcha_token(self, page: Page) -> Optional[str]:
        """Extract hCaptcha token."""
        try:
            token = page.evaluate("""
                () => {
                    const textarea = document.querySelector('[name="h-captcha-response"]') ||
                                     document.querySelector('textarea[name*="captcha"]');
                    if (textarea && textarea.value) return textarea.value;
                    return null;
                }
            """)
            if token and len(str(token)) > 10:
                return str(token)
        except Exception:
            pass

        return None

    # ------------------------------------------------------------------ #
    # FunCaptcha Solver
    # ------------------------------------------------------------------ #

    def _solve_funcaptcha(self, page: Page) -> Optional[str]:
        """Solve FunCaptcha/Arkose via browser automation."""
        log.info("Solving FunCaptcha...")

        deadline = time.time() + self._timeout

        # Find Arkose iframe
        iframe = self._find_iframe(page, ["arkoselabs", "funcaptcha", "fc-"], deadline)
        if not iframe:
            return None

        # Get bounding box
        try:
            box = iframe.bounding_box()
            if not box:
                return None
        except Exception:
            return None

        # Move mouse to iframe area
        x = box["x"] + box["width"] / 2 + random.uniform(-20, 20)
        y = box["y"] + box["height"] / 2 + random.uniform(-10, 10)
        self._human_move(page, x, y)

        # Try to interact with the challenge
        try:
            frame_page = iframe

            # Look for game board / challenge elements
            challenge = frame_page.locator(".challenge-container, #game-core-frame, .fc-game")
            if challenge.count() > 0:
                log.info("FunCaptcha challenge detected")
                # This requires solving the visual puzzle
                # For now, return None to indicate manual intervention needed
                return None

            # Try clicking any interactive elements
            buttons = frame_page.locator("button, .button, [role='button']")
            if buttons.count() > 0:
                buttons.first.click()
                time.sleep(2)

        except Exception as exc:
            log.debug("FunCaptcha interaction failed: %s", exc)

        return None

    # ------------------------------------------------------------------ #
    # Utility Methods
    # ------------------------------------------------------------------ #

    def _find_iframe(self, page: Page, patterns: list[str], deadline: float) -> Optional[object]:
        """Find iframe matching any of the given patterns."""
        while time.time() < deadline:
            for frame in page.frames:
                frame_url = (frame.url or "").lower()
                for pattern in patterns:
                    if pattern in frame_url:
                        # Try to get the iframe element
                        try:
                            iframe_el = page.locator(f"iframe[src*='{pattern}']")
                            if iframe_el.count() > 0:
                                return iframe_el.first.content_frame()
                        except Exception:
                            pass

            time.sleep(0.5)

        return None

    def _human_move(self, page: Page, x: float, y: float) -> None:
        """Simulate human-like mouse movement."""
        # Start from random position
        start_x = random.uniform(100, 500)
        start_y = random.uniform(100, 400)

        steps = random.randint(8, 15)
        for i in range(steps):
            t = (i + 1) / steps
            ease = t * t * (3 - 2 * t)  # Quadratic ease-in-out
            cx = start_x + (x - start_x) * ease + random.uniform(-2, 2)
            cy = start_y + (y - start_y) * ease + random.uniform(-2, 2)
            page.mouse.move(cx, cy)
            time.sleep(random.uniform(0.01, 0.03))

    def _human_click(self, page: Page, x: float, y: float) -> None:
        """Simulate human-like click."""
        self._human_move(page, x, y)
        time.sleep(random.uniform(0.05, 0.15))
        page.mouse.click(x, y)
