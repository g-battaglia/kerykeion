# -*- coding: utf-8 -*-
"""Decide the output format: ``-f`` → the ``-o`` suffix → ``$KERYKEION_CLI_FORMAT`` → text on a TTY, JSON when piped."""

from __future__ import annotations

import os
from pathlib import Path

from kerykeion.extra.cli.io import stdout_is_tty

VALID_FORMATS = ("text", "json", "xml", "svg")
_SUFFIX_FORMATS = {"svg": "svg", "json": "json", "xml": "xml", "txt": "text", "text": "text"}


def suffix_format(output_path: str) -> str | None:
    """A format inferred from an ``-o`` path's extension, if recognised."""
    return _SUFFIX_FORMATS.get(Path(output_path).suffix.lower().lstrip("."))


def resolve_format(explicit: str | None, output_path: str | None) -> str:
    if explicit:
        if explicit not in VALID_FORMATS:
            raise ValueError(f"unknown format {explicit!r}; choose from {', '.join(VALID_FORMATS)}")
        return explicit
    inferred = suffix_format(output_path) if output_path else None
    env = os.environ.get("KERYKEION_CLI_FORMAT")
    return inferred or (env if env in VALID_FORMATS else None) or ("text" if stdout_is_tty() else "json")
