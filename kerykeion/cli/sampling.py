# -*- coding: utf-8 -*-
"""Pre-flight sampling-limit check for ephemeris/transit time series.

``EphemerisDataFactory`` materialises one ``AstrologicalSubjectModel`` per
sample, so a multi-year range at a fine step is an OOM risk before it is a
correctness one. The library guards itself with ``max_days`` / ``max_hours`` /
``max_minutes`` defaults (730 / 8760 / 525600) that raise a bare ``ValueError``
*after* starting — which surfaces as exit 4 (bad input), not the dedicated
exit 8, and only after the work has begun.

We do better: read the ceilings off the factory's own signature (so they can
never drift from the library), count the samples from the requested range and
step **before** constructing anything, and raise :class:`SamplingLimitError`
(mapped to exit 8) if the count is too high. ``--no-limit`` skips the check
*and* passes ``max_*=None`` to disable the library guard too.
"""

from __future__ import annotations

import inspect
from datetime import datetime
from typing import Literal

from kerykeion.cli.errors import SamplingLimitError

StepType = Literal["days", "hours", "minutes"]

_STEP_TO_PARAM = {"days": "max_days", "hours": "max_hours", "minutes": "max_minutes"}
# Rough human hint per ceiling, for the error message.
_HINT = {
    "days": "≈ 2 years of daily points",
    "hours": "≈ 1 year of hourly points",
    "minutes": "≈ 1 year of per-minute points",
}


def _ceiling_for(step_type: StepType) -> int | None:
    """The library's own sample ceiling for *step_type*, read off the signature."""
    from kerykeion import EphemerisDataFactory

    default = inspect.signature(EphemerisDataFactory.__init__).parameters[
        _STEP_TO_PARAM[step_type]
    ].default
    return default if isinstance(default, int) else None


def count_samples(start: datetime, end: datetime, step_type: StepType, step: int) -> int:
    """Number of points a series from *start* to *end* at *step* would yield.

    Matches the library's own count formula (``span // step + 1``) so the
    pre-check agrees with the guard that would fire anyway.
    """
    if step <= 0:
        raise ValueError("--step must be a positive integer.")
    if end < start:
        raise ValueError("--to must not precede --from.")
    span_seconds = (end - start).total_seconds()
    unit_seconds = {"days": 86_400, "hours": 3_600, "minutes": 60}[step_type]
    span_units = int(span_seconds // unit_seconds)
    return span_units // step + 1


def check_ephemeris_sampling(
    start: datetime, end: datetime, step_type: StepType, step: int
) -> None:
    """Raise :class:`SamplingLimitError` (exit 8) if the series is too large."""
    n_samples = count_samples(start, end, step_type, step)
    ceiling = _ceiling_for(step_type)
    if ceiling is not None and n_samples > ceiling:
        raise SamplingLimitError(
            f"Requested {n_samples:,} {step_type} of ephemeris data; the ceiling is "
            f"{ceiling:,} ({_HINT[step_type]}). Narrow the date range, increase "
            "--step, or pass --no-limit to override (at your own risk)."
        )
