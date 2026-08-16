"""Custom CAPTCHA solver — no external services.

Solves CAPTCHAs using:
1. Pattern recognition
2. Request analysis
3. Token extraction
4. Cookie manipulation
"""

from __future__ import annotations

import logging
import os
import re
import time
from typing import Optional

log = logging.getLogger(__name__)


class CaptchaSolver:
    """Custom CAPTCHA solver without external services.

    Uses local logic to solve CAPTCHAs.
    """

    def __init__(self):
        self._solved_count = 0

    def solve_datadome(self, cookies: dict, headers: dict) -> Optional[str]:
        """Attempt to solve DataDome CAPTCHA.

        Strategy:
        1. Check if already solved (valid cookie)
        2. Extract challenge parameters
        3. Generate solution based on pattern
        4. Return token if solved
        """
        # Check for existing DataDome cookie
        dd_cookie = cookies.get("datadome", "")
        if dd_cookie and len(dd_cookie) > 50:
            log.info("DataDome already solved (cookie present)")
            return dd_cookie

        # Check for challenge cookie
        challenge = cookies.get("datadome_captcha_challenge", "")
        if challenge:
            log.info("DataDome challenge detected")
            # Attempt to solve based on challenge type
            return self._solve_challenge_pattern(challenge, headers)

        return None

    def _solve_challenge_pattern(self, challenge: str, headers: dict) -> Optional[str]:
        """Solve CAPTCHA based on pattern analysis."""
        log.info("Analyzing challenge pattern...")

        # Extract challenge parameters
        params = self._extract_challenge_params(challenge)

        if not params:
            log.warning("Could not extract challenge parameters")
            return None

        # Generate solution based on pattern
        solution = self._generate_solution(params)

        if solution:
            log.info("Generated solution: %s...", solution[:20])
            self._solved_count += 1

        return solution

    def _extract_challenge_params(self, challenge: str) -> dict:
        """Extract parameters from challenge string."""
        params = {}

        # Try to extract CID
        cid_match = re.search(r"cid[=:](\w+)", challenge)
        if cid_match:
            params["cid"] = cid_match.group(1)

        # Try to extract hash
        hash_match = re.search(r"hash[=:](\w+)", challenge)
        if hash_match:
            params["hash"] = hash_match.group(1)

        # Try to extract timestamp
        ts_match = re.search(r"ts[=:](\d+)", challenge)
        if ts_match:
            params["ts"] = ts_match.group(1)

        return params

    def _generate_solution(self, params: dict) -> Optional[str]:
        """Generate solution based on parameters."""
        # For now, return a placeholder solution
        # Real implementation would use pattern matching
        # and request analysis to generate valid tokens
        return None

    def solve_recaptcha_audio(self, audio_data: bytes) -> Optional[str]:
        """Solve reCAPTCHA audio challenge.

        Uses local ASR if available.
        """
        # Check if local Whisper is available
        try:
            return self._local_transcribe(audio_data)
        except Exception:
            log.debug("Local transcription not available")
            return None

    def _local_transcribe(self, audio_data: bytes) -> Optional[str]:
        """Local audio transcription."""
        # Save audio to temp file
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            f.write(audio_data)
            audio_path = f.name

        try:
            # Try to use local Whisper
            import whisper
            model = whisper.load_model("base")
            result = model.transcribe(audio_path)
            return result["text"]
        except ImportError:
            log.debug("whisper not installed")
            return None
        finally:
            try:
                os.unlink(audio_path)
            except Exception:
                pass

    def solve_turnstile(self, page_data: str) -> Optional[str]:
        """Solve Cloudflare Turnstile.

        Uses pattern matching to extract token.
        """
        # Look for token in page data
        token_match = re.search(
            r'name="cf-turnstile-response"[^>]*value="([^"]+)"',
            page_data,
        )
        if token_match:
            return token_match.group(1)

        # Try to extract from JavaScript
        js_match = re.search(
            r"turnstile\.getResponse\(\)\s*\|\|\s*['\"]([^'\"]+)['\"]",
            page_data,
        )
        if js_match:
            return js_match.group(1)

        return None

    def solve_hcaptcha(self, page_data: str) -> Optional[str]:
        """Solve hCaptcha.

        Uses pattern matching to extract token.
        """
        # Look for h-captcha-response
        token_match = re.search(
            r'name="h-captcha-response"[^>]*value="([^"]+)"',
            page_data,
        )
        if token_match:
            return token_match.group(1)

        # Try textarea
        token_match = re.search(
            r'<textarea[^>]*name="h-captcha-response"[^>]*>([^<]+)</textarea>',
            page_data,
        )
        if token_match:
            return token_match.group(1).strip()

        return None

    @property
    def solved_count(self) -> int:
        return self._solved_count
