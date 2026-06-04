# -*- coding: utf-8 -*-
"""Find planetary retrograde/direct stations over a date range.

A *station* is the instant a planet's apparent longitudinal motion reverses: a
**retrograde station** (SR) when it turns from direct to retrograde, a **direct
station** (SD) when it turns back. At that instant the longitudinal speed passes
through zero.

There is no station primitive shared by both ephemeris backends
(``find_station_ut`` is a libephemeris extension, absent on swisseph), so — like
``LunationFinderFactory`` — this stays backend-agnostic: it samples the
longitudinal speed via ``swe.calc_ut(..., FLG_SPEED)`` across the range and, on
every sign change of that speed, bisects to the zero crossing. Speed sign changes
are weeks apart even for Mercury, so a coarse sample step never skips one.

Swiss Ephemeris / libephemeris functions used:
    - swe.calc_ut(jd, planet_id, FLG_SWIEPH | FLG_SPEED)
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import List, Optional

from kerykeion.ephemeris_backend import swe, EPHE_DATA_PATH

from kerykeion.schemas.kr_models import SubscriptableBaseModel
from kerykeion.utilities import (
    datetime_to_julian,
    get_kerykeion_point_from_degree,
    julian_to_datetime,
)
from pydantic import Field

logger = logging.getLogger(__name__)

_EPHE_PATH = EPHE_DATA_PATH

# Geocentric speed flag: the [3] element of calc_ut's first tuple is the
# longitudinal speed in degrees/day (negative when retrograde).
_SPEED_FLAGS = swe.FLG_SWIEPH | swe.FLG_SPEED

# The Sun and Moon never station (they are always direct from Earth), so the
# default set is the seven non-luminary classical/modern planets. Names match
# kerykeion's AstrologicalPoint vocabulary.
_STATION_PLANETS: List[tuple[str, int]] = [
    ("Mercury", swe.MERCURY),
    ("Venus", swe.VENUS),
    ("Mars", swe.MARS),
    ("Jupiter", swe.JUPITER),
    ("Saturn", swe.SATURN),
    ("Uranus", swe.URANUS),
    ("Neptune", swe.NEPTUNE),
    ("Pluto", swe.PLUTO),
]

_PLANET_IDS = {name: pid for name, pid in _STATION_PLANETS}

# Sampling step (days). Stations of the same planet are ≥ ~3 weeks apart (even
# Mercury), so half-day sampling never brackets two stations in one step.
_SAMPLE_STEP_DAYS = 0.5
# Bisection iterations: each halving of a 0.5-day bracket reaches sub-second
# precision well before 40 steps.
_BISECTION_ITERS = 40
# Runaway guard (≈ 270 years at the default step).
_MAX_SAMPLES = 200_000


def _to_utc_naive(dt: datetime) -> datetime:
    """Normalize an offset-aware datetime to naive UTC.

    ``datetime_to_julian`` reads the wall-clock fields and ignores tzinfo, and
    the range is documented as UTC, so an aware input must be converted rather
    than silently treated as if its local wall-clock were UTC.
    """
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


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


def _speed(jd: float, body: int) -> float:
    """Longitudinal speed (deg/day) of ``body`` at ``jd``; negative = retrograde."""
    return float(swe.calc_ut(jd, body, _SPEED_FLAGS)[0][3])


def _bisect_station(body: int, a: float, b: float) -> float:
    """Bisect ``[a, b]`` (speed sign differs at the ends) to the speed zero."""
    sa = _speed(a, body)
    for _ in range(_BISECTION_ITERS):
        mid = (a + b) / 2.0
        sm = _speed(mid, body)
        if sm == 0.0:
            return mid
        if (sa < 0.0) != (sm < 0.0):
            b = mid
        else:
            a, sa = mid, sm
    return (a + b) / 2.0


# =============================================================================
# MODELS
# =============================================================================


class StationModel(SubscriptableBaseModel):
    """A single planetary station (motion reversal)."""

    planet: str = Field(description="Planet name (kerykeion AstrologicalPoint vocabulary)")
    station_type: str = Field(description="SR = retrograde station, SD = direct station")
    julian_day: float = Field(description="Julian Day (UT) of the exact station")
    iso_utc: str = Field(description="ISO 8601 UTC datetime of the exact station")
    sign: str = Field(description="Zodiac sign at the station")
    sign_num: int = Field(description="Zodiac sign number (0=Aries)")
    degree: float = Field(description="Degree within the sign (0-30)")
    ecliptic_longitude: float = Field(description="Absolute ecliptic longitude (0-360)")


class RetrogradeStationsCollectionModel(SubscriptableBaseModel):
    """Ordered list of stations within a Julian Day range."""

    start_jd: float
    end_jd: float
    stations: List[StationModel]


# =============================================================================
# FACTORY
# =============================================================================


class RetrogradeStationFactory:
    """Find planetary retrograde/direct stations within a date range.

    Example:
        >>> from kerykeion import RetrogradeStationFactory
        >>> result = RetrogradeStationFactory.from_iso_range("2026-01-01", "2026-12-31")
        >>> result.stations[0].planet, result.stations[0].station_type
    """

    @staticmethod
    def from_iso_range(
        start_date: str,
        end_date: str,
        planets: Optional[List[str]] = None,
    ) -> RetrogradeStationsCollectionModel:
        """Find stations between two ISO date(time) strings (treated as UTC).

        Args:
            start_date: ISO date or datetime, e.g. ``"2026-01-01"``.
            end_date: ISO date or datetime, e.g. ``"2026-12-31"``.
            planets: Optional subset of planet names. Defaults to Mercury..Pluto.
        """
        start_dt = _to_utc_naive(datetime.fromisoformat(start_date))
        end_dt = _to_utc_naive(datetime.fromisoformat(end_date))
        # A date-only end_date means "through the end of that UTC day"; without
        # this it resolves to midnight and drops any station later that day.
        if "T" not in end_date and " " not in end_date:
            end_dt = end_dt.replace(hour=23, minute=59, second=59, microsecond=999999)
        start_jd = datetime_to_julian(start_dt)
        end_jd = datetime_to_julian(end_dt)
        return RetrogradeStationFactory.from_julian_day(start_jd, end_jd, planets)

    @staticmethod
    def from_julian_day(
        start_jd: float,
        end_jd: float,
        planets: Optional[List[str]] = None,
    ) -> RetrogradeStationsCollectionModel:
        """Find all stations in ``[start_jd, end_jd]``, ordered chronologically.

        Args:
            start_jd: Julian Day (UT) range start.
            end_jd: Julian Day (UT) range end.
            planets: Optional subset of planet names. Defaults to Mercury..Pluto.
        """
        if planets:
            invalid = sorted(set(planets) - set(_PLANET_IDS))
            if invalid:
                raise ValueError(
                    f"Unknown or non-stationing planets: {', '.join(invalid)}. "
                    f"Valid: {', '.join(_PLANET_IDS)}"
                )
            bodies = [(name, _PLANET_IDS[name]) for name in planets]
        else:
            bodies = list(_STATION_PLANETS)

        swe.set_ephe_path(_EPHE_PATH)
        stations: List[StationModel] = []

        if end_jd > start_jd:
            for name, body in bodies:
                stations.extend(
                    RetrogradeStationFactory._scan_planet(name, body, start_jd, end_jd)
                )
            stations.sort(key=lambda s: s.julian_day)

        swe.close()
        return RetrogradeStationsCollectionModel(
            start_jd=start_jd,
            end_jd=end_jd,
            stations=stations,
        )

    @staticmethod
    def _scan_planet(
        name: str, body: int, start_jd: float, end_jd: float
    ) -> List[StationModel]:
        """Walk the range for one planet, bisecting each speed sign change."""
        found: List[StationModel] = []
        jd = start_jd
        prev_speed = _speed(jd, body)
        samples = 0
        while jd < end_jd and samples < _MAX_SAMPLES:
            jd_next = min(jd + _SAMPLE_STEP_DAYS, end_jd)
            next_speed = _speed(jd_next, body)
            # Strictly opposite signs => the speed passed through zero in between.
            if prev_speed * next_speed < 0.0:
                jd_station = _bisect_station(body, jd, jd_next)
                # Direct -> retrograde is a retrograde station (SR); the reverse
                # is a direct station (SD).
                station_type = "SR" if prev_speed > 0.0 else "SD"
                found.append(RetrogradeStationFactory._build(name, station_type, jd_station))
            prev_speed = next_speed
            jd = jd_next
            samples += 1
        return found

    @staticmethod
    def _build(name: str, station_type: str, jd: float) -> StationModel:
        """Build a StationModel with the zodiac position at the station JD."""
        lon = float(swe.calc_ut(jd, _PLANET_IDS[name], swe.FLG_SWIEPH)[0][0]) % 360.0
        point = get_kerykeion_point_from_degree(lon, name, "AstrologicalPoint")
        return StationModel(
            planet=name,
            station_type=station_type,
            julian_day=jd,
            iso_utc=_jd_to_iso(jd),
            sign=point.sign,
            sign_num=point.sign_num,
            degree=round(point.position, 6),
            ecliptic_longitude=round(lon, 6),
        )
