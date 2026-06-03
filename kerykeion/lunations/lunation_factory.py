# -*- coding: utf-8 -*-
"""Find lunation moments (New, First Quarter, Full, Last Quarter) over a range.

There is no dedicated lunation-list primitive in libephemeris/swisseph: the
crossing helpers (``solcross_ut``/``mooncross_ut``) target a *fixed* longitude,
not the moving Sun, so they cannot locate syzygies directly. Instead we build on
``compute_lunar_phase_jd`` (binary search on the Sun-Moon ecliptic separation,
~1 second precision, backend-agnostic) and iterate it across the range.

On each step we find the *soonest* upcoming phase across all requested angles
and advance just past it, so consecutive lunations (~7.4 days apart) are never
skipped regardless of the solver's internal search window.

Swiss Ephemeris / libephemeris functions used (via ``compute_lunar_phase_jd``):
    - swe.calc_ut(jd, swe.SUN/swe.MOON, flags)
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import List, Optional

from kerykeion.ephemeris_backend import swe, EPHE_DATA_PATH

from kerykeion.moon_phase_details.utils import compute_lunar_phase_jd
from kerykeion.schemas.kr_models import KerykeionPointModel, SubscriptableBaseModel
from kerykeion.utilities import (
    datetime_to_julian,
    get_kerykeion_point_from_degree,
    julian_to_datetime,
)
from pydantic import Field

logger = logging.getLogger(__name__)

_EPHE_PATH = EPHE_DATA_PATH

# Phase name -> Sun-Moon ecliptic separation angle (degrees).
_PHASE_ANGLES = {
    "new": 0.0,
    "first_quarter": 90.0,
    "full": 180.0,
    "last_quarter": 270.0,
}

# After finding an occurrence of a phase, advance half a synodic month before
# searching for the next one of the SAME phase. This keeps the search base well
# clear of the just-found event (``compute_lunar_phase_jd`` degenerates and
# returns its own start if called <~1 day after a phase) while staying below the
# ~29.53-day recurrence so the next occurrence is never skipped.
_SEARCH_ADVANCE_DAYS = 15.0

# Hard cap on iterations per phase as a runaway guard (≈ enough for millennia).
_MAX_ITERATIONS = 200_000


def _jd_to_iso(jd: float) -> str:
    """Convert a Julian Day (UT) to an ISO 8601 UTC string with seconds."""
    try:
        dt = julian_to_datetime(jd)
        return (
            f"{dt.year:04d}-{dt.month:02d}-{dt.day:02d}"
            f"T{dt.hour:02d}:{dt.minute:02d}:{dt.second:02d}Z"
        )
    except Exception:  # pragma: no cover - defensive
        return ""


# =============================================================================
# MODELS
# =============================================================================


class LunationModel(SubscriptableBaseModel):
    """A single lunation (New/First Quarter/Full/Last Quarter)."""

    phase: str = Field(description="new | first_quarter | full | last_quarter")
    julian_day: float = Field(description="Julian Day (UT) of the exact phase")
    iso_utc: str = Field(description="ISO 8601 UTC datetime of the exact phase")
    sun: KerykeionPointModel = Field(description="Sun position at the phase")
    moon: KerykeionPointModel = Field(description="Moon position at the phase")


class LunationsCollectionModel(SubscriptableBaseModel):
    """Ordered list of lunations within a Julian Day range."""

    start_jd: float
    end_jd: float
    lunations: List[LunationModel]


# =============================================================================
# FACTORY
# =============================================================================


class LunationFinderFactory:
    """Find lunations within a date range, ordered chronologically.

    Example:
        >>> from kerykeion import LunationFinderFactory
        >>> result = LunationFinderFactory.from_iso_range("2026-01-01", "2026-12-31")
        >>> result.lunations[0].phase, result.lunations[0].iso_utc
    """

    @staticmethod
    def from_iso_range(
        start_date: str,
        end_date: str,
        phases: Optional[List[str]] = None,
    ) -> LunationsCollectionModel:
        """Find lunations between two ISO date(time) strings (treated as UTC).

        Args:
            start_date: ISO date or datetime, e.g. ``"2026-01-01"``.
            end_date: ISO date or datetime, e.g. ``"2026-12-31"``.
            phases: Optional subset of ``new``/``first_quarter``/``full``/``last_quarter``.
        """
        start_dt = datetime.fromisoformat(start_date)
        end_dt = datetime.fromisoformat(end_date)
        # A date-only end_date means "through the end of that UTC day"; without
        # this it resolves to midnight and drops any lunation later that day.
        if "T" not in end_date and " " not in end_date:
            end_dt = end_dt.replace(hour=23, minute=59, second=59, microsecond=999999)
        start_jd = datetime_to_julian(start_dt)
        end_jd = datetime_to_julian(end_dt)
        return LunationFinderFactory.from_julian_day(start_jd, end_jd, phases)

    @staticmethod
    def from_julian_day(
        start_jd: float,
        end_jd: float,
        phases: Optional[List[str]] = None,
    ) -> LunationsCollectionModel:
        """Find all requested lunations in ``[start_jd, end_jd]``.

        Args:
            start_jd: Julian Day (UT) range start.
            end_jd: Julian Day (UT) range end.
            phases: Optional subset of phase names. Defaults to all four.
        """
        swe.set_ephe_path(_EPHE_PATH)

        if phases:
            invalid = sorted(set(phases) - set(_PHASE_ANGLES))
            if invalid:
                raise ValueError(f"Unknown phase names: {', '.join(invalid)}")
            targets = {k: _PHASE_ANGLES[k] for k in phases}
        else:
            targets = dict(_PHASE_ANGLES)

        lunations: List[LunationModel] = []

        if targets and end_jd > start_jd:
            # Iterate each phase independently. Stepping by half a synodic month
            # after each hit keeps the search base clear of the just-found event
            # (avoiding solver degeneracy) without skipping the next occurrence.
            for phase_name, angle in targets.items():
                jd = start_jd
                for _ in range(_MAX_ITERATIONS):
                    hit = compute_lunar_phase_jd(jd, angle, forward=True)
                    if hit is None or hit > end_jd:
                        break
                    lunations.append(LunationFinderFactory._build(phase_name, hit))
                    jd = hit + _SEARCH_ADVANCE_DAYS

            lunations.sort(key=lambda lun: lun.julian_day)

        swe.close()
        return LunationsCollectionModel(
            start_jd=start_jd,
            end_jd=end_jd,
            lunations=lunations,
        )

    @staticmethod
    def _build(phase_name: str, jd: float) -> LunationModel:
        """Build a LunationModel with Sun/Moon positions at the exact phase JD."""
        iflag = swe.FLG_SWIEPH
        sun_lon = float(swe.calc_ut(jd, swe.SUN, iflag)[0][0]) % 360.0
        moon_lon = float(swe.calc_ut(jd, swe.MOON, iflag)[0][0]) % 360.0
        return LunationModel(
            phase=phase_name,
            julian_day=jd,
            iso_utc=_jd_to_iso(jd),
            sun=get_kerykeion_point_from_degree(sun_lon, "Sun", "AstrologicalPoint"),
            moon=get_kerykeion_point_from_degree(moon_lon, "Moon", "AstrologicalPoint"),
        )
