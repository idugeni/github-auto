"""Central configuration — dataclass, env-driven."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class EmailConfig:
    lewattok_api_key: str = field(
        default_factory=lambda: os.getenv("LEWATTOK_API_KEY", "")
    )
    supabase_url: str = field(
        default_factory=lambda: os.getenv("SUPABASE_URL", "")
    )
    supabase_anon_key: str = field(
        default_factory=lambda: os.getenv("SUPABASE_ANON_KEY", "")
    )
    provider: str = field(
        default_factory=lambda: os.getenv("EMAIL_PROVIDER", "lewattok")
    )
    poll_interval: float = 1.5
    otp_timeout: int = 120


@dataclass(frozen=True)
class BrowserConfig:
    headless: bool = field(
        default_factory=lambda: os.getenv("BROWSER_HEADLESS", "false").lower() == "true"
    )
    driver: str = field(
        default_factory=lambda: os.getenv("BROWSER_DRIVER", "camoufox")
    )
    viewport_width: int = 1280
    viewport_height: int = 720
    default_timeout: int = 60_000


@dataclass(frozen=True)
class CaptchaConfig:
    groq_api_key: str = field(
        default_factory=lambda: os.getenv("GROQ_API_KEY", "")
    )
    recaptcha_max_attempts: int = 3
    turnstile_timeout: int = 180


@dataclass(frozen=True)
class ProxyConfig:
    url: Optional[str] = field(
        default_factory=lambda: os.getenv("PROXY_URL")
    )
    file: str = str(BASE_DIR / "config" / "proxies.txt")
    cooldown_seconds: int = 30
    sticky: bool = True


@dataclass(frozen=True)
class RegistrationConfig:
    password: str = field(
        default_factory=lambda: os.getenv("REGISTRATION_PASSWORD", "AutoGen2026!")
    )
    username_prefix: str = "gh"
    username_length: int = 14
    password_length: int = 20


@dataclass(frozen=True)
class PipelineConfig:
    batch_size: int = 1
    delay_base: float = field(
        default_factory=lambda: float(os.getenv("BATCH_DELAY_BASE", "8"))
    )
    delay_jitter: float = field(
        default_factory=lambda: float(os.getenv("BATCH_DELAY_JITTER", "2"))
    )
    max_retries: int = 2
    checkpoint_file: str = str(BASE_DIR / "data" / "checkpoint.json")


@dataclass(frozen=True)
class StorageConfig:
    accounts_file: str = str(BASE_DIR / "data" / "accounts.json")
    results_dir: str = str(BASE_DIR / "data" / "results")
    screenshots_dir: str = str(BASE_DIR / "data" / "results" / "screenshots")


@dataclass(frozen=True)
class LogConfig:
    level: str = field(
        default_factory=lambda: os.getenv("LOG_LEVEL", "INFO")
    )
    json_format: bool = field(
        default_factory=lambda: os.getenv("LOG_JSON", "false").lower() == "true"
    )
    log_dir: str = str(BASE_DIR / "data" / "results" / "logs")


@dataclass(frozen=True)
class AppConfig:
    email: EmailConfig = field(default_factory=EmailConfig)
    browser: BrowserConfig = field(default_factory=BrowserConfig)
    captcha: CaptchaConfig = field(default_factory=CaptchaConfig)
    proxy: ProxyConfig = field(default_factory=ProxyConfig)
    registration: RegistrationConfig = field(default_factory=RegistrationConfig)
    pipeline: PipelineConfig = field(default_factory=PipelineConfig)
    storage: StorageConfig = field(default_factory=StorageConfig)
    log: LogConfig = field(default_factory=LogConfig)


config = AppConfig()
