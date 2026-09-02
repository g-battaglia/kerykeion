# -*- coding: utf-8 -*-
"""Single seam for TTY detection: every "are we interactive?" question goes through :func:`stdout_is_tty`, so the test suite has one function to pin."""

from __future__ import annotations

import sys


def stdout_is_tty() -> bool:
    """True when stdout is connected to a terminal (not piped/redirected)."""
    isatty = getattr(sys.stdout, "isatty", None)
    return bool(isatty() if isatty is not None else False)
