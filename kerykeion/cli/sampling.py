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
from datetime import datetime, timezone
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

    default = inspect.signature(EphemerisDataFactory.__init__).parameters[_STEP_TO_PARAM[step_type]].default
    return default if isinstance(default, int) else None


def _zone(tz_str: str):
    """Resolve *tz_str* to a ZoneInfo, or None if it is unset/unknown."""
    if tz_str is None:
        return None
    try:
        from zoneinfo import ZoneInfo
    except Exception:  # pragma: no cover
        return None
    try:
        return ZoneInfo(tz_str)
    except Exception:
        return None


def _utc_bounds(start: datetime, end: datetime, tz_str: str | None) -> tuple[datetime, datetime]:
    """Return bounds as aware-UTC datetimes for true elapsed-time math.

    The library counts hours and minutes in UTC, so across a DST fall-back a
    wall-clock 48h span is 49 UTC hours. Localizing to *tz_str* then converting
    to UTC makes the subtraction yield that true elapsed time.

    Two subtleties this exists to handle:

    * When *tz_str* is ``None`` we return the bounds unchanged: we can't invent a
      timezone, and the divergence only arises across a DST boundary, which
      requires a known zone.
    * Subtracting two aware datetimes that *share the same* ``tzinfo`` ignores
      the offset (a CPython optimisation documented for ``datetime.__sub__``),
      so ``end - start`` on two ``ZoneInfo``-aware datetimes silently collapses
      back to the wall-clock delta. Converting both to UTC first defeats that.

    Naive bounds are localized with :func:`kerykeion.utilities.localize_naive`
    at ``is_dst=False`` — the same call ``EphemerisDataFactory`` makes — so a
    bound inside a DST fall-back fold resolves to the same UTC instant the
    library would pick, rather than ``replace(tzinfo=tz)``'s ``fold=0`` default.
    """
    if tz_str is None:
        return start, end
    tz = _zone(tz_str)
    if tz is None:
        return start, end
    from kerykeion.utilities import localize_naive

    s = start if start.tzinfo is not None else localize_naive(start, tz, is_dst=False)
    e = end if end.tzinfo is not None else localize_naive(end, tz, is_dst=False)
    return s.astimezone(timezone.utc), e.astimezone(timezone.utc)


def _to_local_naive(dt: datetime, tz_str: str | None) -> datetime:
    """Convert an aware datetime to wall-clock naive in *tz_str*.

    Mirrors ``EphemerisDataFactory._to_local_naive``: naive inputs and inputs
    without a known zone are returned unchanged; aware inputs are converted to
    the zone and stripped of ``tzinfo``. Used for the ``days`` count, which the
    library takes on local calendar days (DST-independent) rather than UTC.
    """
    if dt.tzinfo is None or tz_str is None:
        return dt
    tz = _zone(tz_str)
    if tz is None:
        return dt
    return dt.astimezone(tz).replace(tzinfo=None)


def validate_range(start: datetime, end: datetime) -> None:
    """Validate ``--from``/``--to`` awareness consistency and ordering.

    Always run, independent of ``--no-limit``: ``--no-limit`` is meant to bypass
    the *sample ceiling*, not range validation, so an inverted range still
    surfaces the clean ``--to must not precede --from`` message instead of the
    library's generic mid-run sampling error. Comparing a naive bound against an
    aware one would otherwise raise ``TypeError: can't compare offset-naive and
    offset-aware datetimes``; reject the mix up front with a usable message.
    """
    if (start.tzinfo is None) != (end.tzinfo is None):
        raise ValueError(
            "--from and --to must use the same ISO form (both offset-aware or "
            f"both naive); got {start.isoformat()!r} and {end.isoformat()!r}."
        )
    if end < start:
        raise ValueError("--to must not precede --from.")


def count_samples(
    start: datetime,
    end: datetime,
    step_type: StepType,
    step: int,
    tz_str: str | None = None,
) -> int:
    """Number of points a series from *start* to *end* at *step* would yield.

    Mirrors the library's own count formula per step type, so the pre-flight
    check agrees with the guard that would fire anyway:

    * ``days`` — ``(local_end - local_start).days // step + 1`` on wall-clock
      naive bounds in *tz_str* (DST-independent; a local date is never skipped),
      matching ``EphemerisDataFactory``'s local-naive day difference.
    * ``hours`` / ``minutes`` — ``int(utc_delta_seconds / unit) // step + 1``,
      where the delta is measured in UTC so a DST transition counts the extra
      hour. Pass *tz_str* or the span stays wall-clock and silently disagrees
      with the library near a DST boundary.
    """
    validate_range(start, end)
    if step <= 0:
        raise ValueError("--step must be a positive integer.")
    if step_type == "days":
        local_start = _to_local_naive(start, tz_str)
        local_end = _to_local_naive(end, tz_str)
        span_units = (local_end - local_start).days
    else:
        s_utc, e_utc = _utc_bounds(start, end, tz_str)
        unit_seconds = 3_600 if step_type == "hours" else 60
        span_units = int((e_utc - s_utc).total_seconds() // unit_seconds)
    return span_units // step + 1


def check_ephemeris_sampling(
    start: datetime,
    end: datetime,
    step_type: StepType,
    step: int,
    tz_str: str | None = None,
) -> None:
    """Raise :class:`SamplingLimitError` (exit 8) if the series is too large."""
    n_samples = count_samples(start, end, step_type, step, tz_str=tz_str)
    ceiling = _ceiling_for(step_type)
    if ceiling is not None and n_samples > ceiling:
        raise SamplingLimitError(
            f"Requested {n_samples:,} {step_type} of ephemeris data; the ceiling is "
            f"{ceiling:,} ({_HINT[step_type]}). Narrow the date range, increase "
            "--step, or pass --no-limit to override (at your own risk)."
        )
