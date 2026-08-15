"""Parallel processing for batch account creation."""

from __future__ import annotations

import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Callable, Optional

from src.core.account import Account, AccountStatus
from src.core.store import AccountStore

log = logging.getLogger(__name__)


@dataclass
class WorkerStats:
    """Statistics for parallel worker."""
    total: int = 0
    success: int = 0
    failed: int = 0
    in_progress: int = 0
    start_time: float = 0.0
    errors: list[str] = field(default_factory=list)

    @property
    def elapsed(self) -> float:
        if self.start_time == 0:
            return 0.0
        return time.time() - self.start_time

    @property
    def accounts_per_second(self) -> float:
        if self.elapsed == 0:
            return 0.0
        return (self.success + self.failed) / self.elapsed

    @property
    def eta_seconds(self) -> float:
        if self.accounts_per_second == 0:
            return 0.0
        remaining = self.total - self.success - self.failed
        return remaining / self.accounts_per_second


class ParallelWorker:
    """Parallel account creation worker.

    Uses ThreadPoolExecutor to create multiple accounts concurrently.
    """

    def __init__(
        self,
        store: AccountStore,
        worker_fn: Callable[[dict], Account],
        max_workers: int = 3,
        delay_between: float = 2.0,
    ):
        self._store = store
        self._worker_fn = worker_fn
        self._max_workers = max_workers
        self._delay_between = delay_between
        self._stats = WorkerStats()
        self._running = False

    @property
    def stats(self) -> WorkerStats:
        return self._stats

    def run(
        self,
        count: int,
        on_progress: Optional[Callable[[WorkerStats], None]] = None,
        on_complete: Optional[Callable[[Account], None]] = None,
    ) -> WorkerStats:
        """Run parallel account creation."""
        self._stats = WorkerStats(total=count, start_time=time.time())
        self._running = True

        log.info("Starting parallel worker: %d accounts, %d workers", count, self._max_workers)

        with ThreadPoolExecutor(max_workers=self._max_workers) as executor:
            futures = {}
            for i in range(count):
                if not self._running:
                    break

                future = executor.submit(self._create_account, i)
                futures[future] = i
                self._stats.in_progress += 1

                # Small delay between submissions
                if self._delay_between > 0:
                    time.sleep(self._delay_between / self._max_workers)

            # Process completed futures
            for future in as_completed(futures):
                if not self._running:
                    break

                idx = futures[future]
                try:
                    account = future.result()
                    self._store.save(account)

                    if account.status == AccountStatus.FAILED:
                        self._stats.failed += 1
                        self._stats.errors.append(f"[{idx}] {account.error}")
                    else:
                        self._stats.success += 1

                    if on_complete:
                        on_complete(account)

                except Exception as exc:
                    self._stats.failed += 1
                    self._stats.errors.append(f"[{idx}] {str(exc)}")
                    log.error("Worker %d failed: %s", idx, exc)

                finally:
                    self._stats.in_progress -= 1

                if on_progress:
                    on_progress(self._stats)

        self._running = False
        log.info(
            "Parallel worker finished: %d success, %d failed, %.1fs elapsed",
            self._stats.success,
            self._stats.failed,
            self._stats.elapsed,
        )
        return self._stats

    def _create_account(self, index: int) -> Account:
        """Create a single account (called by worker)."""
        context = {"index": index, "attempt": 0}
        return self._worker_fn(context)

    def stop(self):
        """Stop the worker."""
        self._running = False
        log.info("Parallel worker stop requested")
