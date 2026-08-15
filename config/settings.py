"""Central configuration — dataclass, env-driven.

All values loaded from environment variables.
No hardcoded defaults for sensitive/configurable values.
"""

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
    # Primary: LewatTok
    lewattok_api_key: str = field(
        default_factory=lambda: os.getenv("LEWATTOK_API_KEY", "")
    )
    lewattok_base_url: str = field(
        default_factory=lambda: os.getenv("LEWATTOK_BASE_URL", "https://api.lewattok.web.id")
    )

    # Fallback: Supabase
    supabase_url: str = field(
        default_factory=lambda: os.getenv("SUPABASE_URL", "")
    )
    supabase_anon_key: str = field(
        default_factory=lambda: os.getenv("SUPABASE_ANON_KEY", "")
    )

    # Fallback: Gmail
    gmail_client_id: str = field(
        default_factory=lambda: os.getenv("GMAIL_CLIENT_ID", "")
    )
    gmail_client_secret: str = field(
        default_factory=lambda: os.getenv("GMAIL_CLIENT_SECRET", "")
    )
    gmail_refresh_token: str = field(
        default_factory=lambda: os.getenv("GMAIL_REFRESH_TOKEN", "")
    )

    # Fallback: Mail.tm
    mailtm_api_token: str = field(
        default_factory=lambda: os.getenv("MAILTM_API_TOKEN", "")
    )
    mailtm_base_url: str = field(
        default_factory=lambda: os.getenv("MAILTM_BASE_URL", "https://api.mail.tm")
    )

    # Provider selection
    provider: str = field(
        default_factory=lambda: os.getenv("EMAIL_PROVIDER", "lewattok")
    )
    poll_interval: float = field(
        default_factory=lambda: float(os.getenv("EMAIL_POLL_INTERVAL", "1.5"))
    )
    otp_timeout: int = field(
        default_factory=lambda: int(os.getenv("OTP_TIMEOUT", "120"))
    )


@dataclass(frozen=True)
class BrowserConfig:
    headless: bool = field(
        default_factory=lambda: os.getenv("BROWSER_HEADLESS", "false").lower() == "true"
    )
    driver: str = field(
        default_factory=lambda: os.getenv("BROWSER_DRIVER", "camoufox")
    )
    viewport_width: int = field(
        default_factory=lambda: int(os.getenv("BROWSER_VIEWPORT_WIDTH", "1280"))
    )
    viewport_height: int = field(
        default_factory=lambda: int(os.getenv("BROWSER_VIEWPORT_HEIGHT", "720"))
    )
    default_timeout: int = field(
        default_factory=lambda: int(os.getenv("BROWSER_TIMEOUT", "60000"))
    )


@dataclass(frozen=True)
class CaptchaConfig:
    # Groq Whisper ASR
    groq_api_key: str = field(
        default_factory=lambda: os.getenv("GROQ_API_KEY", "")
    )
    whisper_api_url: str = field(
        default_factory=lambda: os.getenv("WHISPER_API_URL", "https://api.groq.com/openai/v1")
    )
    whisper_model: str = field(
        default_factory=lambda: os.getenv("WHISPER_MODEL", "whisper-large-v3-turbo")
    )

    # CapSolver (fallback)
    capsolver_api_key: str = field(
        default_factory=lambda: os.getenv("CAPSOLVER_API_KEY", "")
    )
    capsolver_api_url: str = field(
        default_factory=lambda: os.getenv("CAPSOLVER_API_URL", "https://api.capsolver.com")
    )

    # Settings
    recaptcha_max_attempts: int = field(
        default_factory=lambda: int(os.getenv("RECAPTCHA_MAX_ATTEMPTS", "3"))
    )
    turnstile_timeout: int = field(
        default_factory=lambda: int(os.getenv("TURNSTILE_TIMEOUT", "180"))
    )


@dataclass(frozen=True)
class ProxyConfig:
    url: Optional[str] = field(
        default_factory=lambda: os.getenv("PROXY_URL")
    )
    file: str = field(
        default_factory=lambda: os.getenv("PROXY_FILE", str(BASE_DIR / "config" / "proxies.txt"))
    )
    cooldown_seconds: int = field(
        default_factory=lambda: int(os.getenv("PROXY_COOLDOWN", "30"))
    )
    sticky: bool = field(
        default_factory=lambda: os.getenv("PROXY_STICKY", "true").lower() == "true"
    )

    # Detection
    ip_api_url: str = field(
        default_factory=lambda: os.getenv("IP_API_URL", "http://ip-api.com/json")
    )
    ipinfo_url: str = field(
        default_factory=lambda: os.getenv("IPINFO_URL", "https://ipinfo.io/json")
    )


@dataclass(frozen=True)
class RegistrationConfig:
    password: str = field(
        default_factory=lambda: os.getenv("REGISTRATION_PASSWORD", "")
    )
    username_prefix: str = field(
        default_factory=lambda: os.getenv("USERNAME_PREFIX", "gh")
    )
    username_length: int = field(
        default_factory=lambda: int(os.getenv("USERNAME_LENGTH", "14"))
    )
    password_length: int = field(
        default_factory=lambda: int(os.getenv("PASSWORD_LENGTH", "20"))
    )

    # GitHub URLs
    github_signup_url: str = field(
        default_factory=lambda: os.getenv("GITHUB_SIGNUP_URL", "https://github.com/signup")
    )
    github_home_url: str = field(
        default_factory=lambda: os.getenv("GITHUB_HOME_URL", "https://github.com/")
    )
    github_api_url: str = field(
        default_factory=lambda: os.getenv("GITHUB_API_URL", "https://api.github.com")
    )


@dataclass(frozen=True)
class PipelineConfig:
    batch_size: int = field(
        default_factory=lambda: int(os.getenv("BATCH_SIZE", "1"))
    )
    delay_base: float = field(
        default_factory=lambda: float(os.getenv("BATCH_DELAY_BASE", "8"))
    )
    delay_jitter: float = field(
        default_factory=lambda: float(os.getenv("BATCH_DELAY_JITTER", "2"))
    )
    max_retries: int = field(
        default_factory=lambda: int(os.getenv("MAX_RETRIES", "2"))
    )
    checkpoint_file: str = field(
        default_factory=lambda: os.getenv("CHECKPOINT_FILE", str(BASE_DIR / "data" / "checkpoint.json"))
    )
    max_workers: int = field(
        default_factory=lambda: int(os.getenv("MAX_WORKERS", "3"))
    )


@dataclass(frozen=True)
class StorageConfig:
    accounts_file: str = field(
        default_factory=lambda: os.getenv("ACCOUNTS_FILE", str(BASE_DIR / "data" / "accounts.json"))
    )
    results_dir: str = field(
        default_factory=lambda: os.getenv("RESULTS_DIR", str(BASE_DIR / "data" / "results"))
    )
    screenshots_dir: str = field(
        default_factory=lambda: os.getenv("SCREENSHOTS_DIR", str(BASE_DIR / "data" / "results" / "screenshots"))
    )
    sessions_dir: str = field(
        default_factory=lambda: os.getenv("SESSIONS_DIR", str(BASE_DIR / "data" / "sessions"))
    )
    analytics_file: str = field(
        default_factory=lambda: os.getenv("ANALYTICS_FILE", str(BASE_DIR / "data" / "analytics.json"))
    )


@dataclass(frozen=True)
class LogConfig:
    level: str = field(
        default_factory=lambda: os.getenv("LOG_LEVEL", "INFO")
    )
    json_format: bool = field(
        default_factory=lambda: os.getenv("LOG_JSON", "false").lower() == "true"
    )
    log_dir: str = field(
        default_factory=lambda: os.getenv("LOG_DIR", str(BASE_DIR / "data" / "results" / "logs"))
    )


@dataclass(frozen=True)
class DashboardConfig:
    host: str = field(
        default_factory=lambda: os.getenv("DASHBOARD_HOST", "0.0.0.0")
    )
    port: int = field(
        default_factory=lambda: int(os.getenv("DASHBOARD_PORT", "8000"))
    )
    api_key: str = field(
        default_factory=lambda: os.getenv("API_KEY", "")
    )


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
    dashboard: DashboardConfig = field(default_factory=DashboardConfig)


config = AppConfig()
