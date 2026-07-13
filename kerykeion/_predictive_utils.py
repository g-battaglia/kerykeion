# -*- coding: utf-8 -*-
"""
Shared helpers for predictive factories (midpoints, solar arcs, etc.).

This is part of Kerykeion (C) 2025 Giacomo Battaglia
"""

from __future__ import annotations

import math
from datetime import date
from typing import Iterable, List, Optional, Sequence

from kerykeion.schemas import KerykeionException
from kerykeion.schemas.kr_models import AstrologicalSubjectModel, KerykeionPointModel
from kerykeion.settings.chart_defaults import DEFAULT_CHART_ASPECTS_SETTINGS, DEFAULT_PREDICTIVE_POINTS

PTOLEMAIC_ASPECTS: tuple[str, ...] = (
    "conjunction", "opposition", "trine", "sextile", "square",
)


def is_iso_date_only(value: str) -> bool:
    """Return whether *value* is an ISO date with no time component.

    ``datetime.fromisoformat`` accepts any single character as the date/time
    separator, not only ``T`` or a space. Parsing as ``date`` is therefore the
    reliable way to decide whether an end bound should be widened through the
    end of its UTC day.
    """
    try:
        date.fromisoformat(value)
    except (TypeError, ValueError):
        return False
    return True


def validate_julian_range(start_jd: float, end_jd: float) -> None:
    """Reject non-finite Julian Day bounds before a predictive scan.

    ``NaN`` makes ordering comparisons false and can otherwise turn an invalid
    request into a plausible empty collection. Infinite bounds can escape later
    as backend or datetime-conversion errors. Keeping the check shared gives all
    range factories the same public contract.
    """
    validate_julian_day(start_jd, name="start_jd")
    validate_julian_day(end_jd, name="end_jd")


def validate_julian_day(julian_day: float, *, name: str = "julian_day") -> None:
    """Reject a non-finite Julian Day before calculation or empty fast paths."""
    try:
        is_finite = math.isfinite(julian_day)
    except (OverflowError, TypeError):
        is_finite = False
    if not is_finite:
        raise ValueError(f"{name} must be a finite number")


def jd_to_ymd_hms(jd: float, cal: Optional[int] = None) -> tuple[int, int, int, int, int, int]:
    """Split a Julian Day into integer ``(year, month, day, hour, minute, second)``.

    Uses ``ephe.revjul`` rather than Python ``datetime`` (limited to years
    1..9999) so the BCE range Kerykeion supports decomposes correctly. Rounds
    to the nearest second; an instant that rounds up to 24:00:00 rolls over to
    00:00:00 of the next calendar day (carrying month/year boundaries via
    ``revjul`` in the requested calendar) rather than clamping to 23:59:59.

    Args:
        jd: Julian Day (UT).
        cal: ``ephe.GREG_CAL``/``ephe.JUL_CAL``; defaults to Gregorian.
    """
    from kerykeion.ephemeris_backend import ephe

    if cal is None:
        cal = getattr(ephe, "GREG_CAL", 1)
    year, month, day, hour_frac = ephe.revjul(jd, cal)
    secs = int(hour_frac * 3600 + 0.5)  # nearest second
    if secs >= 86400:
        year, month, day, _ = ephe.revjul(jd + 0.5 / 86400.0, cal)
        secs = 0
    hours, rem = divmod(secs, 3600)
    minutes, seconds = divmod(rem, 60)
    return int(year), int(month), int(day), hours, minutes, seconds


def jd_to_iso_utc(jd: float) -> str:
    """Convert a Julian Day (UT) to an ISO 8601 UTC string with seconds,
    with an extended-year sign for negative (BCE) years.

    Note on the BCE calendar: this uses the proleptic Gregorian calendar (the
    default of ``jd_to_ymd_hms``), which is what ISO 8601 mandates — so an ISO
    event timestamp is standards-conformant. ``AstrologicalSubjectFactory``'s
    BCE birth path instead decomposes year<1 dates in the Julian calendar (the
    historical convention astro.com uses), so a BCE *event* timestamp and a BCE
    *natal chart* date for the same instant differ by the Julian/Gregorian gap
    (~2 days near year 0, growing further back). This is a deliberate
    convention split — ISO strings stay ISO, chart dates stay astrological.
    """
    year, month, day, hours, minutes, seconds = jd_to_ymd_hms(jd)
    year_str = f"-{abs(year):04d}" if year < 0 else f"{year:04d}"
    return f"{year_str}-{month:02d}-{day:02d}T{hours:02d}:{minutes:02d}:{seconds:02d}Z"


def gather_active_points(
    subject: AstrologicalSubjectModel,
    active_points: Optional[Sequence[str]],
) -> List[tuple[str, float]]:
    """Collect ``(name, abs_pos)`` tuples for the requested active points.

    Skips any point that is missing from the subject (e.g. when the
    subject was built with a reduced ``active_points`` list).
    """
    if isinstance(active_points, (str, bytes)):
        raise KerykeionException(
            "`active_points` must be a sequence of point names, not a single string."
        )
    candidate_names: Iterable[str] = DEFAULT_PREDICTIVE_POINTS if active_points is None else active_points

    gathered: List[tuple[str, float]] = []
    seen: set[str] = set()
    for name in candidate_names:
        if not isinstance(name, str):
            raise KerykeionException(
                f"`active_points` entries must be strings; got {type(name).__name__}."
            )
        attr = name.lower()
        if attr in seen:
            continue
        seen.add(attr)
        point = getattr(subject, attr, None)
        if not isinstance(point, KerykeionPointModel):
            continue
        gathered.append((point.name, point.abs_pos))
    return gathered


def build_aspect_settings(orb: float, aspect_filter: Optional[Sequence[str]]) -> list[dict]:
    """Materialise an aspects-settings list with a uniform orb override."""
    if isinstance(aspect_filter, (str, bytes)):
        raise KerykeionException(
            "`aspects` must be a sequence of aspect names, not a single string."
        )
    if not math.isfinite(orb) or orb < 0:
        raise KerykeionException("`aspect_orb` must be a finite non-negative number.")
    settings: list[dict] = []
    for aspect in DEFAULT_CHART_ASPECTS_SETTINGS:
        name = aspect["name"]  # type: ignore[index]
        if aspect_filter is not None and name not in aspect_filter:
            continue
        settings.append(
            {
                "degree": aspect["degree"],  # type: ignore[index]
                "name": name,
                "orb": orb,
            }
        )
    return settings
