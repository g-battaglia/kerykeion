# -*- coding: utf-8 -*-
"""Single seam for TTY detection, so the test suite can monkeypatch one spot.

Rich reads the terminal width from ``os.get_terminal_size()`` on the process's
fds 0/1/2 — not from the ``file`` a :class:`rich.console.Console` wraps — so
``typer.testing.CliRunner`` alone does not isolate output rendering from the
developer's real terminal width. Routing every "are we interactive?" question
through :func:`stdout_is_tty` gives the test suite exactly one function to pin.
"""

from __future__ import annotations

import sys


def stdout_is_tty() -> bool:
    """True when stdout is connected to a terminal (not piped/redirected)."""
    isatty = getattr(sys.stdout, "isatty", None)
    return bool(isatty() if isatty is not None else False)
