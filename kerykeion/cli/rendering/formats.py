# -*- coding: utf-8 -*-
"""Decide which output format a command should produce.

Precedence (highest wins): an explicit ``-f/--format`` flag → the file suffix of
``-o/--output`` → ``$KERYKEION_CLI_FORMAT`` → TTY detection (text on a terminal,
JSON when piped). The TTY check goes through :func:`kerykeion.cli.io.stdout_is_tty`
so tests can pin it from one place.
"""

from __future__ import annotations

import os
from pathlib import Path

from kerykeion.cli.io import stdout_is_tty

VALID_FORMATS = ("text", "json", "xml", "svg")

_SUFFIX_BY_EXT = {
    "svg": "svg",
    "json": "json",
    "xml": "xml",
    "txt": "text",
    "text": "text",
}


def suffix_format(output_path: str) -> str | None:
    """Infer a format from an ``-o`` path's extension, if recognised."""
    return _SUFFIX_BY_EXT.get(Path(output_path).suffix.lower().lstrip("."))


def resolve_format(explicit: str | None, output_path: str | None) -> str:
    """Pick the output format for this invocation (see module docstring)."""
    if explicit:
        if explicit not in VALID_FORMATS:
            raise ValueError(f"unknown format {explicit!r}; choose from {', '.join(VALID_FORMATS)}")
        return explicit
    if output_path:
        inferred = suffix_format(output_path)
        if inferred:
            return inferred
    env = os.environ.get("KERYKEION_CLI_FORMAT")
    if env and env in VALID_FORMATS:
        return env
    return "text" if stdout_is_tty() else "json"
