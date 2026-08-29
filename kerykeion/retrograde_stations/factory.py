# -*- coding: utf-8 -*-
"""Find planetary retrograde/direct stations over a date range.

A *station* is the instant a planet's apparent longitudinal motion reverses: a
**retrograde station** (SR) when it turns from direct to retrograde, a **direct
station** (SD) when it turns back. At that instant the longitudinal speed passes
through zero.

There is no station primitive shared by both ephemeris backends
(``find_station_ut`` is a libephemeris extension, absent on swisseph), so — like
``LunationFinderFactory`` — this stays backend-agnostic: it samples the
longitudinal speed via ``ephe.calc_ut(..., FLG_SPEED)`` across the range and, on
every sign change of that speed, bisects to the zero crossing. Speed sign changes
are weeks apart even for Mercury, so a coarse sample step never skips one.

Swiss Ephemeris / libephemeris functions used:
    - ephe.calc_ut(jd, planet_id, FLG_SWIEPH | FLG_SPEED)
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import List, Optional, cast

from kerykeion.ephemeris_backend.backend import ephe, ephemeris_session
from kerykeion.settings.config_constants import POINT_NUMBER_MAP
from kerykeion.predictive.utils import is_iso_date_only, jd_to_iso_utc as _jd_to_iso, validate_julian_bounds

from kerykeion.schemas.exceptions import KerykeionException
from kerykeion.schemas.literals import AstrologicalPoint, SiderealMode, ZodiacType
from kerykeion.schemas.models import SubscriptableBaseModel
from kerykeion.utilities.core import (
    datetime_to_julian,
    get_kerykeion_point_from_degree,
)
from pydantic import Field

logger = logging.getLogger(__name__)

# Geocentric speed flag: the [3] element of calc_ut's first tuple is the
# longitudinal speed in degrees/day (negative when retrograde).
_SPEED_FLAGS = ephe.FLG_SWIEPH | ephe.FLG_SPEED

# The Sun and Moon never station (they are always direct from Earth), so the
# default set is the seven non-luminary classical/modern planets. Names match
# kerykeion's AstrologicalPoint vocabulary.
_STATION_PLANETS: List[tuple[str, int]] = [
    (name, POINT_NUMBER_MAP[name])
    for name in ("Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto")
]

_PLANET_IDS = {name: pid for name, pid in _STATION_PLANETS}
# Chiron stations too; opt-in (``planets=[..., "Chiron"]``) so the default
# output — and its baselines — stay the seven classical/modern planets.
_PLANET_IDS["Chiron"] = POINT_NUMBER_MAP["Chiron"]

# Sampling step (days). Stations of the same planet are ≥ ~3 weeks apart (even
# Mercury), so a week-long step still never brackets two stations — the speed
# sign changes at most once per interval and bisection finds the unique zero.
_SAMPLE_STEP_DAYS = 7.0
# Bisection to sub-millisecond on a 7-day bracket — the ISO output is rounded
# to the second, so further halvings buy nothing.
_BISECTION_ITERS = 30
# Backstop on samples per scan (~38,000 years at the 7-day step). Ranges that
# would exceed it are rejected explicitly rather than silently truncated.
_MAX_SAMPLES = 2_000_000
# A station within one second of the range start decides the initial motion
# state deterministically, instead of leaving it to the sign of a speed that
# is numerically ~0 there.
_EDGE_TOL_DAYS = 1.0 / 86400.0


def _to_utc_naive(dt: datetime) -> datetime:
    """Normalize an offset-aware datetime to naive UTC.

    ``datetime_to_julian`` reads the wall-clock fields and ignores tzinfo, and
    the range is documented as UTC, so an aware input must be converted rather
    than silently treated as if its local wall-clock were UTC.
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
                "sidereal_mode='USER' requires custom ayanamsha parameters, which RetrogradeStationFactory does not accept."
            )
        if not hasattr(ephe, f"SIDM_{sidereal_mode}"):
            raise KerykeionException(f"Unknown sidereal_mode: {sidereal_mode!r}.")


def _speed(jd: float, body: int) -> float:
    """Longitudinal speed (deg/day) of ``body`` at ``jd``; negative = retrograde."""
    try:
        return float(ephe.calc_ut(jd, body, _SPEED_FLAGS)[0][3])
    except Exception as exc:
        # Range errors (libephemeris EphemerisRangeError, swisseph.Error)
        # propagate raw from calc_ut — normalize them to the documented
        # exception type, like the lunation factory does.
        raise KerykeionException(
            f"Station search failed at JD {jd:.5f}: {exc}. This usually means "
            f"the date falls outside the available ephemeris range; narrow "
            f"the date range."
        ) from exc


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


def _ensure_scannable(start_jd: float, end_jd: float) -> None:
    """Reject ranges too long to scan, so a caller never receives a silently
    truncated result whose ``end_jd`` still claims the full requested range."""
    if (end_jd - start_jd) / _SAMPLE_STEP_DAYS > _MAX_SAMPLES:
        raise ValueError(
            f"Date range too large to scan at the current resolution "
            f"(> {_MAX_SAMPLES} samples). Narrow the date range."
        )


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


class RetrogradePeriodModel(SubscriptableBaseModel):
    """One span of retrograde motion, clipped to the requested range.

    ``start`` is a retrograde station (or the range start, flagged), ``end`` a
    direct station (or the range end, flagged). Periods carry no sign: station
    instants are zodiac-independent.
    """

    planet: str = Field(description="Planet name (kerykeion AstrologicalPoint vocabulary)")
    start_jd: float = Field(description="Julian Day (UT) the retrograde motion begins (clipped to the range start)")
    end_jd: float = Field(description="Julian Day (UT) the retrograde motion ends (clipped to the range end)")
    start: str = Field(description="ISO 8601 UTC of start_jd")
    end: str = Field(description="ISO 8601 UTC of end_jd")
    start_clipped: bool = Field(description="True when the planet was already retrograde at the range start")
    end_clipped: bool = Field(description="True when the planet is still retrograde at the range end")


class RetrogradePeriodsCollectionModel(SubscriptableBaseModel):
    """Retrograde spans of every requested planet across a Julian Day range."""

    start_jd: float
    end_jd: float
    periods: List[RetrogradePeriodModel]


def _probe_start(start_jd: float, body: int) -> float:
    """``start_jd`` minus the one-second boundary probe, or ``start_jd`` itself
    when that second lies before the ephemeris begins."""
    probe = start_jd - _EDGE_TOL_DAYS
    try:
        _speed(probe, body)
    except KerykeionException:
        return start_jd
    return probe


def _fold_retrograde_periods(
    name: str, retro_at_start: bool, stations: List[StationModel], start_jd: float, end_jd: float
) -> List[RetrogradePeriodModel]:
    """Turn the motion state at the range start plus the in-range stations into
    retrograde spans: SR opens, SD closes, the edges clip."""

    def period(a: float, b: float, a_clipped: bool, b_clipped: bool) -> RetrogradePeriodModel:
        return RetrogradePeriodModel(
            planet=name,
            start_jd=a,
            end_jd=b,
            start=_jd_to_iso(a),
            end=_jd_to_iso(b),
            start_clipped=a_clipped,
            end_clipped=b_clipped,
        )

    ordered = sorted(stations, key=lambda s: s.julian_day)
    # A station on the range's first second overrides the speed snapshot: the
    # motion BEFORE an SR is direct, before an SD it is retrograde. Such a
    # station is the range start itself (the scan may place it a hair before).
    if ordered and abs(ordered[0].julian_day - start_jd) <= _EDGE_TOL_DAYS:
        retro_at_start = ordered[0].station_type == "SD"
        ordered[0] = ordered[0].model_copy(update={"julian_day": start_jd})

    out: List[RetrogradePeriodModel] = []
    open_jd: Optional[float] = start_jd if retro_at_start else None
    open_clipped = retro_at_start
    for station in ordered:
        if station.station_type == "SR":
            if open_jd is not None:
                raise KerykeionException(
                    f"{name}: retrograde station at JD {station.julian_day:.5f} while already retrograde."
                )
            open_jd, open_clipped = station.julian_day, False
        else:
            if open_jd is None:
                raise KerykeionException(
                    f"{name}: direct station at JD {station.julian_day:.5f} while not retrograde."
                )
            if station.julian_day - open_jd > _EDGE_TOL_DAYS:
                out.append(period(open_jd, station.julian_day, open_clipped, False))
            open_jd = None
    if open_jd is not None and end_jd - open_jd > _EDGE_TOL_DAYS:
        out.append(period(open_jd, end_jd, open_clipped, True))
    return out


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
        zodiac_type: ZodiacType = "Tropical",
        sidereal_mode: Optional[SiderealMode] = None,
    ) -> RetrogradeStationsCollectionModel:
        """Find stations between two ISO date(time) strings (treated as UTC).

        Args:
            start_date: ISO date or datetime, e.g. ``"2026-01-01"``.
            end_date: ISO date or datetime, e.g. ``"2026-12-31"``.
            planets: Optional subset of planet names. Defaults to Mercury..Pluto.
            zodiac_type: ``"Tropical"`` (default) or ``"Sidereal"``. A station is
                the instant longitudinal speed passes through zero, computed in
                the tropical frame, so the station TIMES are zodiac-independent;
                only the reported sign shifts under a sidereal zodiac.
            sidereal_mode: Ayanamsha when ``zodiac_type='Sidereal'``.
        """
        try:
            start_dt = _to_utc_naive(datetime.fromisoformat(start_date))
            end_dt = _to_utc_naive(datetime.fromisoformat(end_date))
        except (ValueError, TypeError) as exc:
            # Wrap the bare datetime error as the library's own exception, so a
            # caller catching KerykeionException around this entry point is not
            # broken by a malformed ISO start_date/end_date. Same contract as
            # LunationFinderFactory.from_iso_range.
            raise KerykeionException(
                f"Invalid ISO date/datetime for station range "
                f"(start_date={start_date!r}, end_date={end_date!r}): {exc}"
            ) from exc
        # A date-only end means "through the end of that UTC day". Parsing it
        # as a date avoids misclassifying datetime.fromisoformat's other valid
        # one-character separators (for example ``_``).
        if is_iso_date_only(end_date):
            end_dt = end_dt.replace(hour=23, minute=59, second=59, microsecond=999999)
        start_jd = datetime_to_julian(start_dt)
        end_jd = datetime_to_julian(end_dt)
        return RetrogradeStationFactory.from_julian_day(start_jd, end_jd, planets, zodiac_type, sidereal_mode)

    @staticmethod
    def from_julian_day(
        start_jd: float,
        end_jd: float,
        planets: Optional[List[str]] = None,
        zodiac_type: ZodiacType = "Tropical",
        sidereal_mode: Optional[SiderealMode] = None,
    ) -> RetrogradeStationsCollectionModel:
        """Find all stations in ``[start_jd, end_jd]``, ordered chronologically.

        Args:
            start_jd: Julian Day (UT) range start.
            end_jd: Julian Day (UT) range end.
            planets: Optional subset of planet names. Defaults to Mercury..Pluto.
            zodiac_type: ``"Tropical"`` (default) or ``"Sidereal"``. Station
                TIMES are zodiac-independent; only the reported sign shifts.
            sidereal_mode: Ayanamsha when ``zodiac_type='Sidereal'``.

        Raises:
            KerykeionException: For an invalid zodiac configuration, or if the
                ephemeris backend fails mid-scan (most often a date outside the
                available ephemeris range); the scan never returns silently
                truncated results.
            ValueError: If a planet name is unknown, either Julian bound is
                non-finite, or the range is too large to scan.
        """
        validate_julian_bounds(start_jd, end_jd)

        # None = default set; an explicit empty list = scan nothing.
        if planets is not None:
            invalid = sorted(set(planets) - set(_PLANET_IDS))
            if invalid:
                raise ValueError(
                    f"Unknown or non-stationing planets: {', '.join(invalid)}. "
                    f"Valid: {', '.join(_PLANET_IDS)}"
                )
            # Deduplicate (preserve order): duplicates would repeat the scan and
            # emit every event multiple times.
            bodies = [(name, _PLANET_IDS[name]) for name in dict.fromkeys(planets)]
        else:
            bodies = list(_STATION_PLANETS)

        _validate_zodiac(zodiac_type, sidereal_mode)

        stations: List[StationModel] = []
        if end_jd > start_jd and bodies:
            _ensure_scannable(start_jd, end_jd)
            # The session holds the ephemeris lock across the whole scan (calc_ut
            # reads process-global backend state shared with chart calculations)
            # and resets that state on exit without degrading the backend. Its
            # iflag carries FLG_SIDEREAL for a sidereal zodiac and is used ONLY
            # for the reported sign in _build; the speed-zero station search
            # stays tropical (see _speed), so the station TIMES never shift.
            with ephemeris_session(zodiac_type=zodiac_type, sidereal_mode=sidereal_mode) as iflag:
                for name, body in bodies:
                    stations.extend(
                        RetrogradeStationFactory._scan_planet(name, body, start_jd, end_jd, iflag)
                    )
            stations.sort(key=lambda s: s.julian_day)

        return RetrogradeStationsCollectionModel(
            start_jd=start_jd,
            end_jd=end_jd,
            stations=stations,
        )

    @staticmethod
    def retrograde_periods_from_iso_range(
        start_date: str,
        end_date: str,
        planets: Optional[List[str]] = None,
        zodiac_type: ZodiacType = "Tropical",
        sidereal_mode: Optional[SiderealMode] = None,
    ) -> RetrogradePeriodsCollectionModel:
        """Retrograde spans between two ISO date(time) strings (treated as UTC).

        Same arguments as :meth:`from_iso_range`; ``"Chiron"`` is accepted on
        request.
        """
        try:
            start_dt = _to_utc_naive(datetime.fromisoformat(start_date))
            end_dt = _to_utc_naive(datetime.fromisoformat(end_date))
        except (ValueError, TypeError) as exc:
            raise KerykeionException(
                f"Invalid ISO date/datetime for station range "
                f"(start_date={start_date!r}, end_date={end_date!r}): {exc}"
            ) from exc
        if is_iso_date_only(end_date):
            end_dt = end_dt.replace(hour=23, minute=59, second=59, microsecond=999999)
        return RetrogradeStationFactory.retrograde_periods_from_julian_day(
            datetime_to_julian(start_dt), datetime_to_julian(end_dt), planets, zodiac_type, sidereal_mode
        )

    @staticmethod
    def retrograde_periods_from_julian_day(
        start_jd: float,
        end_jd: float,
        planets: Optional[List[str]] = None,
        zodiac_type: ZodiacType = "Tropical",
        sidereal_mode: Optional[SiderealMode] = None,
    ) -> RetrogradePeriodsCollectionModel:
        """Retrograde spans of each planet across ``[start_jd, end_jd]``, clipped to it.

        The motion state at the range start is read from the longitudinal speed
        there; the in-range stations open (SR) and close (SD) the spans; spans
        touching an edge are clipped and flagged. Beyond a one-second probe
        before the range start (to catch a station sitting on it), nothing is
        searched outside the range, so a span open at the edge does not tell
        where its real station is. An empty or inverted range yields none.

        Raises:
            KerykeionException: as :meth:`from_julian_day`, and when the
                stations do not alternate (SR while retrograde, SD while direct).
            ValueError: as :meth:`from_julian_day`.
        """
        validate_julian_bounds(start_jd, end_jd)
        if planets is not None:
            invalid = sorted(set(planets) - set(_PLANET_IDS))
            if invalid:
                raise ValueError(
                    f"Unknown or non-stationing planets: {', '.join(invalid)}. "
                    f"Valid: {', '.join(_PLANET_IDS)}"
                )
            bodies = [(name, _PLANET_IDS[name]) for name in dict.fromkeys(planets)]
        else:
            bodies = list(_STATION_PLANETS)
        _validate_zodiac(zodiac_type, sidereal_mode)

        periods: List[RetrogradePeriodModel] = []
        if end_jd > start_jd and bodies:
            _ensure_scannable(start_jd, end_jd)
            with ephemeris_session(zodiac_type=zodiac_type, sidereal_mode=sidereal_mode) as iflag:
                for name, body in bodies:
                    retro_at_start = _speed(start_jd, body) < 0.0
                    # Start the scan one second early: a station sitting on the
                    # range start is then bracketed and found, and the fold's
                    # edge rule decides the initial state from it rather than
                    # from a speed that is numerically ~0 there. At the very
                    # edge of the ephemeris that second does not exist: then
                    # the scan starts on the range and the snapshot decides.
                    stations = RetrogradeStationFactory._scan_planet(
                        name, body, _probe_start(start_jd, body), end_jd, iflag
                    )
                    periods.extend(_fold_retrograde_periods(name, retro_at_start, stations, start_jd, end_jd))

        return RetrogradePeriodsCollectionModel(start_jd=start_jd, end_jd=end_jd, periods=periods)

    @staticmethod
    def _scan_planet(
        name: str, body: int, start_jd: float, end_jd: float, iflag: int
    ) -> List[StationModel]:
        """Walk the range for one planet, bisecting each speed sign change.

        The speed sampling (``_speed``/``_bisect_station``) is tropical, so the
        station instants are frame-independent; ``iflag`` is passed to ``_build``
        only to report the sign in the requested (possibly sidereal) frame.
        """
        found: List[StationModel] = []
        jd = start_jd
        prev_speed = _speed(jd, body)
        if prev_speed == 0.0 and start_jd < end_jd:
            # A station exactly on the range's first sample: boundary zeros are
            # claimed on `next` (so zeros shared by two intervals count once),
            # which can never fire for the very first sample — classify it from
            # the following motion instead of dropping it.
            first_next_speed = _speed(min(start_jd + _SAMPLE_STEP_DAYS, end_jd), body)
            if first_next_speed != 0.0:
                station_type = "SR" if first_next_speed < 0.0 else "SD"
                found.append(RetrogradeStationFactory._build(name, station_type, start_jd, iflag))
        while jd < end_jd:
            jd_next = min(jd + _SAMPLE_STEP_DAYS, end_jd)
            next_speed = _speed(jd_next, body)
            # A sign change in speed brackets a station; an endpoint speed of
            # exactly 0.0 is the station itself. Claim a boundary zero on next
            # (not prev) so a zero shared by two intervals is counted once.
            crossed = prev_speed * next_speed < 0.0
            endpoint_zero = next_speed == 0.0 and prev_speed != 0.0
            if crossed or endpoint_zero:
                jd_station = jd_next if endpoint_zero else _bisect_station(body, jd, jd_next)
                # Direct -> retrograde is a retrograde station (SR); the reverse
                # is a direct station (SD). prev_speed is non-zero in both branches.
                station_type = "SR" if prev_speed > 0.0 else "SD"
                found.append(RetrogradeStationFactory._build(name, station_type, jd_station, iflag))
            prev_speed = next_speed
            jd = jd_next
        return found

    @staticmethod
    def _build(name: str, station_type: str, jd: float, iflag: int) -> StationModel:
        """Build a StationModel with the zodiac position at the station JD.

        ``iflag`` is the enclosing session's flag: for a sidereal zodiac it
        carries ``FLG_SIDEREAL``, so the reported longitude/sign is sidereal
        while the station JD (found from the tropical speed) is unchanged.
        """
        try:
            lon = float(ephe.calc_ut(jd, _PLANET_IDS[name], iflag)[0][0]) % 360.0
        except Exception as exc:
            # Same normalization as _speed: the station JD lies inside a
            # bracket whose endpoints already computed, so this is practically
            # unreachable — but the documented contract is KerykeionException.
            raise KerykeionException(
                f"Station search failed at JD {jd:.5f}: {exc}. This usually "
                f"means the date falls outside the available ephemeris range; "
                f"narrow the date range."
            ) from exc
        # name is validated against _PLANET_IDS upstream, so it is a known point name.
        point = get_kerykeion_point_from_degree(lon, cast(AstrologicalPoint, name), "AstrologicalPoint")
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
