# -*- coding: utf-8 -*-
"""Small helpers shared across the command modules.

These are the trivial compositions every command would otherwise duplicate
verbatim: resolving the output format and routing the payload through the
warnings funnel (:func:`_emit`), flattening a repeatable/CSV option
(:func:`_split_csv`), and parsing an ISO date/datetime (:func:`_parse_dt`).
Kept here so a behaviour change (e.g. a newly accepted datetime form) lands in
exactly one place rather than five.

This module is a leaf: it imports only the CLI ``warnings``/``formats`` helpers
and the stdlib, never another command module, so importing it can never cycle.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from kerykeion.cli import warnings
from kerykeion.cli.rendering import formats


def _emit(model: object, fmt: Optional[str], output: Optional[str]) -> None:
    """Resolve the format and route the payload through the warnings funnel."""
    warnings.output_with_warnings(model, formats.resolve_format(fmt, output), output)


def _split_csv(values: Optional[list[str]]) -> Optional[list[str]]:
    """Flatten a repeatable option that may also carry comma-separated tokens."""
    if values is None:
        return None
    out: list[str] = []
    for item in values:
        out.extend(part.strip() for part in item.split(",") if part.strip())
    return out or None


def _parse_dt(value: str) -> datetime:
    """Parse an ISO date or datetime, with a usable error otherwise."""
    try:
        return datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(
            f"expected an ISO date or datetime (YYYY-MM-DD or YYYY-MM-DDThh:mm), got {value!r}"
        ) from exc
