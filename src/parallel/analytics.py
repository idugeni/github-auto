"""Analytics and metrics tracking."""

from __future__ import annotations

import json
import logging
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)


@dataclass
class AccountMetrics:
    """Metrics for a single account creation."""
    username: str
    email: str
    start_time: float
    end_time: float = 0.0
    status: str = "pending"
    error: str = ""
    proxy: str = ""
    email_provider: str = ""
    captcha_solved: bool = False
    otp_wait_time: float = 0.0

    @property
    def duration(self) -> float:
        if self.end_time == 0:
            return 0.0
        return self.end_time - self.start_time

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class AnalyticsSummary:
    """Aggregated analytics data."""
    total_accounts: int = 0
    success_count: int = 0
    failed_count: int = 0
    avg_duration: float = 0.0
    min_duration: float = 0.0
    max_duration: float = 0.0
    success_rate: float = 0.0
    captcha_solve_rate: float = 0.0
    avg_otp_wait: float = 0.0
    errors_by_type: dict[str, int] = field(default_factory=dict)
    timestamp: str = ""


class Analytics:
    """Track and analyze account creation metrics."""

    def __init__(self, data_file: str = "data/analytics.json"):
        self._data_file = Path(data_file)
        self._metrics: list[AccountMetrics] = []
        self._load()

    def _load(self) -> None:
        """Load metrics from file."""
        if self._data_file.exists():
            try:
                data = json.loads(self._data_file.read_text(encoding="utf-8"))
                self._metrics = [AccountMetrics(**m) for m in data]
            except Exception as exc:
                log.warning("Failed to load analytics: %s", exc)

    def _save(self) -> None:
        """Save metrics to file."""
        self._data_file.parent.mkdir(parents=True, exist_ok=True)
        data = [m.to_dict() for m in self._metrics]
        self._data_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def record_start(self, username: str, email: str, proxy: str = "", **kwargs) -> None:
        """Record account creation start."""
        metric = AccountMetrics(
            username=username,
            email=email,
            start_time=time.time(),
            proxy=proxy,
            email_provider=kwargs.get("email_provider", ""),
        )
        self._metrics.append(metric)

    def record_success(self, username: str, captcha_solved: bool = False, otp_wait: float = 0.0) -> None:
        """Record account creation success."""
        for m in reversed(self._metrics):
            if m.username == username:
                m.end_time = time.time()
                m.status = "success"
                m.captcha_solved = captcha_solved
                m.otp_wait_time = otp_wait
                break
        self._save()

    def record_failure(self, username: str, error: str) -> None:
        """Record account creation failure."""
        for m in reversed(self._metrics):
            if m.username == username:
                m.end_time = time.time()
                m.status = "failed"
                m.error = error
                break
        self._save()

    def get_summary(self, last_n: Optional[int] = None) -> AnalyticsSummary:
        """Get analytics summary."""
        metrics = self._metrics[-last_n:] if last_n else self._metrics
        if not metrics:
            return AnalyticsSummary(timestamp=time.strftime("%Y-%m-%d %H:%M:%S"))

        completed = [m for m in metrics if m.end_time > 0]
        successful = [m for m in completed if m.status == "success"]
        failed = [m for m in completed if m.status == "failed"]

        durations = [m.duration for m in completed]
        otp_waits = [m.otp_wait_time for m in successful if m.otp_wait_time > 0]

        # Count errors by type
        errors_by_type: dict[str, int] = {}
        for m in failed:
            error_type = m.error.split(":")[0] if m.error else "unknown"
            errors_by_type[error_type] = errors_by_type.get(error_type, 0) + 1

        return AnalyticsSummary(
            total_accounts=len(metrics),
            success_count=len(successful),
            failed_count=len(failed),
            avg_duration=sum(durations) / len(durations) if durations else 0.0,
            min_duration=min(durations) if durations else 0.0,
            max_duration=max(durations) if durations else 0.0,
            success_rate=len(successful) / len(completed) * 100 if completed else 0.0,
            captcha_solve_rate=sum(1 for m in successful if m.captcha_solved) / len(successful) * 100 if successful else 0.0,
            avg_otp_wait=sum(otp_waits) / len(otp_waits) if otp_waits else 0.0,
            errors_by_type=errors_by_type,
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
        )

    def get_recent(self, count: int = 10) -> list[dict]:
        """Get recent metrics."""
        return [m.to_dict() for m in self._metrics[-count:]]

    def clear(self) -> None:
        """Clear all metrics."""
        self._metrics.clear()
        self._save()
