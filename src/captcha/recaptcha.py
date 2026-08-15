"""reCAPTCHA audio ASR solver (ported from autoregister-account)."""

from __future__ import annotations

import logging
import os
import tempfile
import time
from typing import Optional

from playwright.sync_api import Page

from .base import CaptchaSolver

log = logging.getLogger(__name__)


class RecaptchaAudioSolver(CaptchaSolver):
    """Solve reCAPTCHA via audio challenge + Groq Whisper ASR."""

    def __init__(self, groq_api_key: Optional[str] = None, max_attempts: int = 3):
        self._api_key = groq_api_key or os.getenv("GROQ_API_KEY", "")
        self._max_attempts = max_attempts
        self._client = None

    def _get_client(self):
        if self._client is None:
            if not self._api_key:
                raise RuntimeError("GROQ_API_KEY required for reCAPTCHA ASR")
            from openai import OpenAI
            self._client = OpenAI(
                api_key=self._api_key,
                base_url="https://api.groq.com/openai/v1",
            )
        return self._client

    def _download_audio(self, url: str) -> str:
        """Download audio file and return path."""
        import requests
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        path = os.path.join(tempfile.gettempdir(), f"captcha_{int(time.time())}.mp3")
        with open(path, "wb") as f:
            f.write(resp.content)
        return path

    def _transcribe(self, audio_path: str) -> str:
        """Transcribe audio via Groq Whisper."""
        client = self._get_client()
        with open(audio_path, "rb") as f:
            result = client.audio.transcriptions.create(
                model="whisper-large-v3-turbo",
                file=f,
                language="en",
            )
        return result.text

    @staticmethod
    def _clean_text(text: str) -> str:
        """Clean transcribed text."""
        import re
        text = re.sub(r"\.{2,}", "", text)
        text = re.sub(r"[^a-zA-Z0-9\s]", "", text)
        return text.strip().lower()

    def solve(self, page: Page, url: Optional[str] = None) -> Optional[str]:
        """Solve reCAPTCHA audio challenge on page."""
        if not self._api_key:
            log.warning("No GROQ_API_KEY, skipping reCAPTCHA solve")
            return None

        try:
            return self._solve_attempt(page)
        except Exception as exc:
            log.warning("reCAPTCHA solve failed: %s", exc)
            return None

    def _solve_attempt(self, page: Page) -> Optional[str]:
        """Single solve attempt."""
        # Find reCAPTCHA iframe
        frames = page.frames
        anchor_frame = None
        for frame in frames:
            if "recaptcha/anchor" in (frame.url or ""):
                anchor_frame = frame
                break

        if not anchor_frame:
            log.debug("No reCAPTCHA anchor frame found")
            return None

        # Check if already solved
        try:
            checked = anchor_frame.locator("#recaptcha-anchor").get_attribute(
                "aria-checked", timeout=2000
            )
            if checked == "true":
                log.info("reCAPTCHA already solved")
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
                log.info("reCAPTCHA solved instantly (no challenge)")
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
            log.debug("No reCAPTCHA challenge frame found")
            return None

        # Click audio button
        try:
            audio_btn = challenge_frame.locator("#rc-audiochallenge-instructions-link")
            if audio_btn.count() > 0:
                audio_btn.click()
                time.sleep(1)
        except Exception:
            log.debug("No audio button found, may be Enterprise reCAPTCHA")
            return None

        # Download audio
        for attempt in range(self._max_attempts):
            try:
                audio_link = challenge_frame.locator("#rc-audiochallenge-download-link")
                if audio_link.count() == 0:
                    audio_link = challenge_frame.locator("a[href*='audio']")
                if audio_link.count() == 0:
                    time.sleep(1.5)
                    continue

                audio_url = audio_link.get_attribute("href")
                if not audio_url:
                    time.sleep(1.5)
                    continue

                audio_path = self._download_audio(audio_url)

                # Transcribe
                text = self._transcribe(audio_path)
                cleaned = self._clean_text(text)
                log.info("Transcribed reCAPTCHA: '%s'", cleaned)

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
                        log.info("reCAPTCHA audio solved successfully")
                        return "audio_solved"
                except Exception:
                    pass

                # Cleanup
                try:
                    os.unlink(audio_path)
                except Exception:
                    pass

            except Exception as exc:
                log.debug("Audio solve attempt %d failed: %s", attempt + 1, exc)

        return None
