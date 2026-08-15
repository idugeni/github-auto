"""Batch pipeline orchestrator."""

from __future__ import annotations

import json
import logging
import random
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from .account import Account, AccountStatus
from .store import AccountStore

log = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    total: int = 0
    success: int = 0
    failed: int = 0
    skipped: int = 0
    elapsed: float = 0.0
    errors: list[str] | None = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class Pipeline:
    """Batch account creation pipeline with checkpointing."""

    def __init__(
        self,
        store: AccountStore,
        worker: Callable[[dict], Account],
        delay_base: float = 8.0,
        delay_jitter: float = 2.0,
        max_retries: int = 2,
        checkpoint_file: Optional[str] = None,
    ):
        self._store = store
        self._worker = worker
        self._delay_base = delay_base
        self._delay_jitter = delay_jitter
        self._max_retries = max_retries
        self._checkpoint_path = Path(checkpoint_file or "data/checkpoint.json")

    def _compute_delay(self) -> float:
        jitter = random.uniform(0, self._delay_jitter)
        return self._delay_base + jitter

    def _load_checkpoint(self) -> int:
        if self._checkpoint_path.exists():
            try:
                data = json.loads(self._checkpoint_path.read_text())
                return data.get("last_index", 0)
            except Exception:
                pass
        return 0

    def _save_checkpoint(self, index: int) -> None:
        self._checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
        self._checkpoint_path.write_text(
            json.dumps({"last_index": index}), encoding="utf-8"
        )

    def _clear_checkpoint(self) -> None:
        if self._checkpoint_path.exists():
            self._checkpoint_path.unlink()

    def run(
        self,
        count: int = 1,
        resume: bool = False,
        on_success: Optional[Callable[[Account], None]] = None,
        on_failure: Optional[Callable[[Account, Exception], None]] = None,
        on_progress: Optional[Callable[[int, int], None]] = None,
    ) -> PipelineResult:
        """Run the pipeline for N accounts."""
        result = PipelineResult()
        start_index = self._load_checkpoint() if resume else 0
        result.total = count

        log.info(
            "Pipeline started: %d accounts (resume from %d)", count, start_index
        )

        for i in range(start_index, count):
            attempt = 0
            while attempt <= self._max_retries:
                try:
                    account = self._worker({"index": i, "attempt": attempt})
                    self._store.save(account)
                    result.success += 1
                    if on_success:
                        on_success(account)
                    log.info(
                        "[%d/%d] OK: %s (%s)",
                        i + 1, count, account.username, account.email,
                    )
                    break
                except Exception as exc:
                    attempt += 1
                    log.warning(
                        "[%d/%d] Attempt %d failed: %s",
                        i + 1, count, attempt, exc,
                    )
                    if attempt > self._max_retries:
                        result.failed += 1
                        result.errors.append(str(exc))
                        if on_failure:
                            on_failure(
                                Account(
                                    username=f"failed_{i}",
                                    password="",
                                    email="",
                                    status=AccountStatus.FAILED,
                                    error=str(exc),
                                ),
                                exc,
                            )

            self._save_checkpoint(i + 1)
            if on_progress:
                on_progress(i + 1, count)

            if i < count - 1:
                delay = self._compute_delay()
                log.debug("Delaying %.1fs before next account", delay)
                time.sleep(delay)

        self._clear_checkpoint()
        result.elapsed = time.time() - start_index  # approximate
        log.info(
            "Pipeline finished: %d success, %d failed",
            result.success, result.failed,
        )
        return result
