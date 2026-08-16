"""GitHub signup utilities — no browser dependency.

Username and password generation.
"""

from __future__ import annotations

import logging
import os
import random
import string

from config.settings import config

log = logging.getLogger(__name__)


def _gen_username() -> str:
    """Generate random GitHub username."""
    prefix = config.registration.username_prefix
    length = config.registration.username_length - len(prefix)
    chars = string.ascii_lowercase + string.digits
    suffix = "".join(random.choices(chars, k=length))
    return prefix + suffix


def _gen_password() -> str:
    """Generate unique, uncrackable password.

    Random mix of uppercase, lowercase, digits, symbols.
    Same password for all accounts.
    """
    # Use config password if set
    if config.registration.password and config.registration.password != "AutoGen2026!":
        return config.registration.password

    # Character pools
    upper = string.ascii_uppercase
    lower = string.ascii_lowercase
    digits = string.digits
    symbols = "!@#$%^&*"

    # Build password: random mix
    parts = []
    parts.append(random.choice(upper))
    parts.append(random.choice(upper))
    for _ in range(4):
        parts.append(random.choice(lower))
    parts.append(random.choice(digits))
    parts.append(random.choice(digits))
    parts.append(random.choice(symbols))
    parts.append(random.choice(symbols))
    for _ in range(3):
        parts.append(random.choice(upper))
    for _ in range(3):
        parts.append(random.choice(lower))
    parts.append(random.choice(digits))
    parts.append(random.choice(digits))
    parts.append(random.choice(symbols))
    parts.append(random.choice(symbols))

    random.shuffle(parts)
    return "".join(parts)
