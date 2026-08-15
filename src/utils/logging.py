"""Structured logging with loguru."""

from __future__ import annotations

import sys
from pathlib import Path

from loguru import logger

from config.settings import config

_initialized = False


def setup_logging() -> None:
    """Configure loguru with console + file handlers."""
    global _initialized
    if _initialized:
        return
    _initialized = True

    logger.remove()

    fmt = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )

    logger.add(
        sys.stderr,
        format=fmt,
        level=config.log.level,
        colorize=True,
    )

    log_dir = Path(config.log.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    logger.add(
        str(log_dir / "github-auto_{time:YYYY-MM-DD}.log"),
        format=fmt,
        level=config.log.level,
        rotation="10 MB",
        retention="7 days",
        compression="gz",
    )


def get_logger(name: str | None = None):
    """Get a bound logger instance."""
    setup_logging()
    if name:
        return logger.bind(module=name)
    return logger
