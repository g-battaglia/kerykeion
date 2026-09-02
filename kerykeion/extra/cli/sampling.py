# -*- coding: utf-8 -*-
"""Pre-flight sampling-limit check for the ephemeris/transit time series.

``EphemerisDataFactory`` builds one subject per sample, so a multi-year range at
a fine step is an OOM risk first. The library's own ``max_days``/``max_hours``/
``max_minutes`` guard also fires before any computation, but as a bare
``ValueError`` (exit 4) worded for a Python caller; this counts the samples
first — from the same ceilings, read off the factory's signature so they cannot
drift — and raises ``SamplingLimitError`` (exit 8) naming the flags to change.
"""

from __future__ import annotations

import inspect
from datetime import datetime, timezone
from typing import Literal

from kerykeion.extra.cli.errors import SamplingLimitError

StepType = Literal["days", "hours", "minutes"]

_CEILING_PARAM = {"days": "max_days", "hours": "max_hours", "minutes": "max_minutes"}
_HINT = {
    "days": "≈ 2 years of daily points",
    "hours": "≈ 1 year of hourly points",
    "minutes": "≈ 1 year of per-minute points",
}


def _ceiling_for(step_type: StepType) -> int | None:
    from kerykeion import EphemerisDataFactory

    default = inspect.signature(EphemerisDataFactory.__init__).parameters[_CEILING_PARAM[step_type]].default
    return default if isinstance(default, int) else None


def _zone(tz_str: str | None):
    """``ZoneInfo`` for *tz_str*, or ``None`` if unset or unknown."""
    if tz_str is None:
        return None
    from zoneinfo import ZoneInfo

    try:
        return ZoneInfo(tz_str)
    except Exception:
        return None


def _utc_bounds(start: datetime, end: datetime, tz_str: str | None) -> tuple[datetime, datetime]:
    """Aware-UTC bounds, so hours/minutes count true elapsed time across a DST change.

    Naive bounds are localised with ``localize_naive(is_dst=False)`` — the call
    the factory makes — so a bound inside a fall-back fold lands on the same
    instant. Both go to UTC before subtraction: two datetimes sharing a
    ``tzinfo`` subtract by wall clock, which would collapse the DST hour.
    """
    tz = _zone(tz_str)
    if tz is None:
        return start, end
    from kerykeion.utilities import localize_naive

    s = start if start.tzinfo is not None else localize_naive(start, tz, is_dst=False)
    e = end if end.tzinfo is not None else localize_naive(end, tz, is_dst=False)
    return s.astimezone(timezone.utc), e.astimezone(timezone.utc)


def _to_local_naive(dt: datetime, tz_str: str | None) -> datetime:
    """An aware datetime as wall-clock naive in *tz_str* (mirrors the factory); naive/unknown-zone inputs unchanged."""
    tz = _zone(tz_str) if dt.tzinfo is not None else None
    return dt.astimezone(tz).replace(tzinfo=None) if tz is not None else dt


def validate_range(start: datetime, end: datetime) -> None:
    """Reject a naive/aware mix and an inverted range — always, ``--no-limit`` bypasses only the ceiling."""
    if (start.tzinfo is None) != (end.tzinfo is None):
        raise ValueError(
            "--from and --to must use the same ISO form (both offset-aware or both naive); "
            f"got {start.isoformat()!r} and {end.isoformat()!r}."
        )
    if end < start:
        raise ValueError("--to must not precede --from.")


def count_samples(start: datetime, end: datetime, step_type: StepType, step: int, tz_str: str | None = None) -> int:
    """The number of points a series would yield — the library's own formula per step type.

    ``days`` counts local calendar days in *tz_str* (DST-independent); ``hours``
    and ``minutes`` count in UTC, so a DST transition counts its extra hour.
    """
    validate_range(start, end)
    if step <= 0:
        raise ValueError("--step must be a positive integer.")
    if step_type == "days":
        span_units = (_to_local_naive(end, tz_str) - _to_local_naive(start, tz_str)).days
    else:
        s_utc, e_utc = _utc_bounds(start, end, tz_str)
        span_units = int((e_utc - s_utc).total_seconds() // (3_600 if step_type == "hours" else 60))
    return span_units // step + 1


def check_ephemeris_sampling(
    start: datetime, end: datetime, step_type: StepType, step: int, tz_str: str | None = None
) -> None:
    """Raise ``SamplingLimitError`` (exit 8) if the series is too large."""
    n_samples = count_samples(start, end, step_type, step, tz_str=tz_str)
    ceiling = _ceiling_for(step_type)
    if ceiling is not None and n_samples > ceiling:
        raise SamplingLimitError(
            f"Requested {n_samples:,} {step_type} of ephemeris data; the ceiling is {ceiling:,} "
            f"({_HINT[step_type]}). Narrow the date range, increase --step, or pass --no-limit to override "
            "(at your own risk)."
        )
