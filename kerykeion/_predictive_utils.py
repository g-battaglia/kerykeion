# -*- coding: utf-8 -*-
"""
Shared helpers for predictive factories (midpoints, solar arcs, etc.).

This is part of Kerykeion (C) 2025 Giacomo Battaglia
"""

from __future__ import annotations

import math
from typing import Iterable, List, Optional, Sequence

from kerykeion.schemas import KerykeionException
from kerykeion.schemas.kr_models import AstrologicalSubjectModel, KerykeionPointModel
from kerykeion.settings.chart_defaults import DEFAULT_CHART_ASPECTS_SETTINGS, DEFAULT_PREDICTIVE_POINTS

PTOLEMAIC_ASPECTS: tuple[str, ...] = (
    "conjunction", "opposition", "trine", "sextile", "square",
)


def jd_to_iso_utc(jd: float) -> str:
    """Convert a Julian Day (UT) to an ISO 8601 UTC string with seconds.

    Uses ``ephe.revjul`` rather than Python ``datetime`` (limited to years
    1..9999) so the BCE range Kerykeion supports formats correctly, with an
    extended-year sign for negative years. Instants that round up to 24:00:00
    roll over to 00:00:00 of the next calendar day (carrying month/year
    boundaries via ``revjul``) rather than clamping to 23:59:59.
    """
    from kerykeion.ephemeris_backend import ephe

    year, month, day, hour_frac = ephe.revjul(jd)
    secs = int(hour_frac * 3600 + 0.5)  # nearest second
    if secs >= 86400:
        year, month, day, _ = ephe.revjul(jd + 0.5 / 86400.0)
        secs = 0
    hours, rem = divmod(secs, 3600)
    minutes, seconds = divmod(rem, 60)
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
