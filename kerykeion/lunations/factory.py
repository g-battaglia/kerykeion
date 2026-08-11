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
    - ephe.calc_ut(jd, ephe.SUN/ephe.MOON, flags)
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import List, Optional

from kerykeion.ephemeris_backend import ephe, ephemeris_session
from kerykeion._predictive_utils import is_iso_date_only, jd_to_iso_utc as _jd_to_iso, validate_julian_bounds

from kerykeion.moon_phase_details.utils import compute_lunar_phase_jd
from kerykeion.schemas.exceptions import KerykeionException
from kerykeion.schemas.literals import SiderealMode, ZodiacType
from kerykeion.schemas.models import KerykeionPointModel, SubscriptableBaseModel
from kerykeion.utilities import (
    datetime_to_julian,
    get_kerykeion_point_from_degree,
)
from pydantic import Field

logger = logging.getLogger(__name__)

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

# Max angular error (deg) for a solver hit to count as a real phase. A genuine
# hit converges to <0.001°; a degenerate echo of the search start is degrees off.
_PHASE_ANGLE_TOL = 0.01


def _to_utc_naive(dt: datetime) -> datetime:
    """Normalize an offset-aware datetime to naive UTC.

    ``datetime_to_julian`` reads the wall-clock fields and ignores tzinfo, and
    the lunation range is documented as UTC, so an aware input must be converted
    rather than silently treated as if its local wall-clock were UTC.
    """
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def _validate_zodiac(zodiac_type: ZodiacType, sidereal_mode: Optional[SiderealMode]) -> None:
    """Validate the zodiac configuration before opening an ephemeris session.

    Same contract as ``VoidOfCourseMoonFactory``'s validator: pure validation,
    no global ephemeris state touched.
    """
    if zodiac_type not in ("Tropical", "Sidereal"):
        raise KerykeionException(f"Unknown zodiac_type: {zodiac_type!r} (expected 'Tropical' or 'Sidereal').")

    if zodiac_type == "Sidereal":
        if sidereal_mode is None:
            raise KerykeionException("sidereal_mode is required when zodiac_type='Sidereal'.")
        if sidereal_mode == "USER":
            raise KerykeionException(
                "sidereal_mode='USER' requires custom ayanamsha parameters, which LunationFinderFactory does not accept."
            )
        if not hasattr(ephe, f"SIDM_{sidereal_mode}"):
            raise KerykeionException(f"Unknown sidereal_mode: {sidereal_mode!r}.")


def _phase_angle_error(jd: float, target_angle: float) -> float:
    """Absolute error (deg) between the actual Sun-Moon separation at ``jd`` and
    ``target_angle``. Used to reject degenerate ``compute_lunar_phase_jd`` echoes
    that return the search start instead of a real syzygy."""
    sun = float(ephe.calc_ut(jd, ephe.SUN, ephe.FLG_SWIEPH)[0][0]) % 360.0
    moon = float(ephe.calc_ut(jd, ephe.MOON, ephe.FLG_SWIEPH)[0][0]) % 360.0
    diff = (moon - sun - target_angle) % 360.0
    return min(diff, 360.0 - diff)



def _ensure_scannable(start_jd: float, end_jd: float) -> None:
    """Reject ranges too long to scan, so a caller never receives a silently
    truncated result whose ``end_jd`` still claims the full requested range."""
    if (end_jd - start_jd) / _SEARCH_ADVANCE_DAYS > _MAX_ITERATIONS:
        raise ValueError(
            f"Date range too large to scan at the current resolution "
            f"(> {_MAX_ITERATIONS} search steps per phase). Narrow the date range."
        )


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
        zodiac_type: ZodiacType = "Tropical",
        sidereal_mode: Optional[SiderealMode] = None,
    ) -> LunationsCollectionModel:
        """Find lunations between two ISO date(time) strings (treated as UTC).

        Args:
            start_date: ISO date or datetime, e.g. ``"2026-01-01"``.
            end_date: ISO date or datetime, e.g. ``"2026-12-31"``.
            phases: Optional subset of ``new``/``first_quarter``/``full``/``last_quarter``.
            zodiac_type: ``"Tropical"`` (default) or ``"Sidereal"``. Phase TIMES
                are the Sun-Moon elongation and are zodiac-independent (the
                ayanamsha cancels in the separation); only the reported Sun/Moon
                signs shift under a sidereal zodiac.
            sidereal_mode: Ayanamsha when ``zodiac_type='Sidereal'``.
        """
        try:
            start_dt = _to_utc_naive(datetime.fromisoformat(start_date))
            end_dt = _to_utc_naive(datetime.fromisoformat(end_date))
        except (ValueError, TypeError) as exc:
            # Wrap the bare datetime error as the library's own exception, so a
            # caller catching KerykeionException around this entry point is not
            # broken by a malformed ISO start_date/end_date.
            raise KerykeionException(
                f"Invalid ISO date/datetime for lunation range "
                f"(start_date={start_date!r}, end_date={end_date!r}): {exc}"
            ) from exc
        # A date-only end_date means "through the end of that UTC day"; without
        # this it resolves to midnight and drops any lunation later that day.
        if is_iso_date_only(end_date):
            end_dt = end_dt.replace(hour=23, minute=59, second=59, microsecond=999999)
        start_jd = datetime_to_julian(start_dt)
        end_jd = datetime_to_julian(end_dt)
        return LunationFinderFactory.from_julian_day(start_jd, end_jd, phases, zodiac_type, sidereal_mode)

    @staticmethod
    def from_julian_day(
        start_jd: float,
        end_jd: float,
        phases: Optional[List[str]] = None,
        zodiac_type: ZodiacType = "Tropical",
        sidereal_mode: Optional[SiderealMode] = None,
    ) -> LunationsCollectionModel:
        """Find all requested lunations in ``[start_jd, end_jd]``.

        Args:
            start_jd: Julian Day (UT) range start.
            end_jd: Julian Day (UT) range end.
            phases: Optional subset of phase names. Defaults to all four.
            zodiac_type: ``"Tropical"`` (default) or ``"Sidereal"``. Phase TIMES
                are zodiac-independent; only the reported Sun/Moon signs shift.
            sidereal_mode: Ayanamsha when ``zodiac_type='Sidereal'``.

        Raises:
            KerykeionException: For an invalid zodiac configuration, or if the
                ephemeris backend fails mid-scan (most often a date outside the
                available ephemeris range); the scan never returns silently
                truncated results.
            ValueError: If a phase name is unknown, either Julian bound is
                non-finite, or the range is too large to scan.
        """
        validate_julian_bounds(start_jd, end_jd)

        # None = default (all four phases); an explicit empty list = scan none.
        # `if phases:` conflated the two, treating phases=[] as "all four" —
        # the opposite of the ingress/station factories, whose planets=[] means
        # "scan nothing". Distinguish on `is not None` for a consistent contract.
        if phases is not None:
            invalid = sorted(set(phases) - set(_PHASE_ANGLES))
            if invalid:
                raise ValueError(f"Unknown phase names: {', '.join(invalid)}")
            targets = {k: _PHASE_ANGLES[k] for k in dict.fromkeys(phases)}
        else:
            targets = dict(_PHASE_ANGLES)

        _validate_zodiac(zodiac_type, sidereal_mode)

        lunations: List[LunationModel] = []

        if targets and end_jd > start_jd:
            _ensure_scannable(start_jd, end_jd)
            # Iterate each phase independently. Stepping by half a synodic month
            # after each hit keeps the search base clear of the just-found event
            # (avoiding solver degeneracy) without skipping the next occurrence.
            # The phase solver (compute_lunar_phase_jd) works on the Sun-Moon
            # elongation, which is frame-independent, so the phase TIMES are
            # identical under a sidereal zodiac; only _build's reported signs
            # shift, via the session iflag (FLG_SIDEREAL).
            with ephemeris_session(zodiac_type=zodiac_type, sidereal_mode=sidereal_mode) as iflag:
                for phase_name, angle in targets.items():
                    jd = start_jd
                    for _ in range(_MAX_ITERATIONS):
                        try:
                            hit = compute_lunar_phase_jd(jd, angle, forward=True)
                        except Exception as exc:
                            # The helper swallows RuntimeError into None, but
                            # range errors (libephemeris EphemerisRangeError,
                            # swisseph.Error) propagate raw — normalize them to
                            # the documented exception type.
                            raise KerykeionException(
                                f"Lunar phase search ('{phase_name}') failed at "
                                f"JD {jd:.5f}: {exc}. This usually means the date "
                                f"falls outside the available ephemeris range; "
                                f"narrow the date range."
                            ) from exc
                        if hit is None:
                            # A lunar phase always recurs within the solver's
                            # 30-day window, so None never means "no more
                            # events": it is the helper swallowing a backend
                            # error (e.g. the scan walked past the edge of the
                            # ephemeris data). Surface it instead of silently
                            # truncating a result that still claims the full
                            # requested range.
                            raise KerykeionException(
                                f"Lunar phase search ('{phase_name}') failed at "
                                f"JD {jd:.5f}: the ephemeris backend could not "
                                f"compute Sun/Moon positions. This usually means "
                                f"the date falls outside the available ephemeris "
                                f"range; narrow the date range."
                            )
                        if hit > end_jd:
                            break
                        # compute_lunar_phase_jd can echo its own start (a tiny step
                        # past jd) when called just after a phase, reporting an event
                        # whose true angle is not the target. Record only genuine hits.
                        if _phase_angle_error(hit, angle) <= _PHASE_ANGLE_TOL:
                            lunations.append(LunationFinderFactory._build(phase_name, hit, iflag))
                        jd = hit + _SEARCH_ADVANCE_DAYS

            lunations.sort(key=lambda lun: lun.julian_day)

        return LunationsCollectionModel(
            start_jd=start_jd,
            end_jd=end_jd,
            lunations=lunations,
        )

    @staticmethod
    def _build(phase_name: str, jd: float, iflag: int) -> LunationModel:
        """Build a LunationModel with Sun/Moon positions at the exact phase JD.

        ``iflag`` is the enclosing session's flag: for a sidereal zodiac it
        carries ``FLG_SIDEREAL``, so the reported Sun/Moon longitudes (and hence
        signs) are sidereal while the phase JD itself is unchanged.
        """
        sun_lon = float(ephe.calc_ut(jd, ephe.SUN, iflag)[0][0]) % 360.0
        moon_lon = float(ephe.calc_ut(jd, ephe.MOON, iflag)[0][0]) % 360.0
        return LunationModel(
            phase=phase_name,
            julian_day=jd,
            iso_utc=_jd_to_iso(jd),
            sun=get_kerykeion_point_from_degree(sun_lon, "Sun", "AstrologicalPoint"),
            moon=get_kerykeion_point_from_degree(moon_lon, "Moon", "AstrologicalPoint"),
        )
