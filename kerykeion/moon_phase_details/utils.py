# -*- coding: utf-8 -*-
"""
Moon Phase Details Utilities

This module contains low-level astronomical helpers used by the
MoonPhaseDetailsFactory. All functions in this module are pure utilities:
they work with primitive types (floats, datetimes, etc.) and do not depend
on Pydantic models or application-level classes.

Responsibilities:
    - Time conversions (datetime <-> Julian Day)
    - Sidereal time computation
    - Coordinate transformations (equatorial -> horizontal)
    - Precise sunrise/sunset calculation via Swiss Ephemeris
    - Global solar and lunar eclipse search via Swiss Ephemeris

These helpers keep the main factory module focused on building domain models
and orchestrating the overall moon phase context, while encapsulating the
astronomical and numerical details here.
"""

from __future__ import annotations

import logging
import math
from datetime import datetime, timezone
from typing import Optional
from kerykeion.ephemeris_backend import ephe, EPHE_DATA_PATH
from kerykeion.schemas.exceptions import KerykeionException
from kerykeion.utilities import wrap_180

logger = logging.getLogger(__name__)


# The "expected calculation failed → degrade to None" handlers below must catch
# the backend's own error (libephemeris raises its ``Error`` hierarchy — incl.
# ``EphemerisRangeError`` near the ephemeris edge; pyswisseph raises
# ``swisseph.Error``), NOT ``RuntimeError`` which no backend raises. Resolve the
# type once, module-level, so the ``except`` clauses stay mypy-clean (a bare
# ``getattr(ephe, "Error", …)`` inline in an ``except`` is untyped ``Any``).
_BACKEND_ERRORS: tuple = tuple({RuntimeError, getattr(ephe, "Error", RuntimeError)})


# ---------------------------------------------------------------------------
# Swiss Ephemeris compatibility shims and constants
# ---------------------------------------------------------------------------

# Different swisseph builds expose eclipse flags with or without the SE_ prefix.
ECL_TOTAL = getattr(ephe, "SE_ECL_TOTAL", getattr(ephe, "ECL_TOTAL", 0))
ECL_ANNULAR_TOTAL = getattr(ephe, "SE_ECL_ANNULAR_TOTAL", getattr(ephe, "ECL_ANNULAR_TOTAL", 0))
ECL_ANNULAR = getattr(ephe, "SE_ECL_ANNULAR", getattr(ephe, "ECL_ANNULAR", 0))
ECL_PARTIAL = getattr(ephe, "SE_ECL_PARTIAL", getattr(ephe, "ECL_PARTIAL", 0))
ECL_PENUMBRAL = getattr(ephe, "SE_ECL_PENUMBRAL", getattr(ephe, "ECL_PENUMBRAL", 0))

# Distance unit conversion: Astronomical Unit to kilometers.
# IAU 2012 nominal value: 1 AU = 149,597,870.700 km exactly
# Source: https://www.iau.org/static/resolutions/IAU2012_English.pdf
AU_KM = getattr(ephe, "AUNIT", 149597870.7)

# Standard meteorological conditions at sea level for atmospheric refraction calculations
# Used by Swiss Ephemeris rise/set routines to compute apparent horizon
# Source: Standard atmosphere (ISO 2533:1975)
STANDARD_ATMOSPHERIC_PRESSURE_HPA = 1013.25  # hectopascals (sea level)
STANDARD_TEMPERATURE_CELSIUS = 15.0  # degrees Celsius



def safe_parse_iso_datetime(value: Optional[str]) -> datetime:
    """
    Parse an ISO formatted datetime string into an aware UTC datetime.

    This helper is tolerant about the *format*:
        - Accepts both standard ISO strings and those ending with 'Z'
        - Treats naive datetimes as UTC

    It is strict about *invalid input*: an empty or unparseable value raises
    a :class:`KerykeionException` instead of silently falling back to the
    current UTC time, which produced a plausible-looking but wrong result
    downstream.

    Raises:
        KerykeionException: If ``value`` is empty/None or not a valid ISO
            datetime string.
    """
    if not value:
        raise KerykeionException(
            "Cannot parse ISO datetime: value is empty or None."
        )

    try:
        dt = datetime.fromisoformat(value)
    except (TypeError, ValueError):
        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except Exception as exc:
            raise KerykeionException(
                f"Cannot parse ISO datetime {value!r}: {exc}"
            ) from exc

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    return dt.astimezone(timezone.utc)


def describe_solar_eclipse_type(retflag: int) -> str:
    """
    Map Swiss Ephemeris eclipse flags to a human-readable solar eclipse type.
    """
    if retflag & ECL_TOTAL:
        return "Total Solar Eclipse"
    if retflag & ECL_ANNULAR_TOTAL:
        return "Hybrid Solar Eclipse"
    if retflag & ECL_ANNULAR:
        return "Annular Solar Eclipse"
    if retflag & ECL_PARTIAL:
        return "Partial Solar Eclipse"
    return "Solar Eclipse"


def describe_lunar_eclipse_type(retflag: int) -> str:
    """
    Map Swiss Ephemeris eclipse flags to a human-readable lunar eclipse type.
    """
    if retflag & ECL_TOTAL:
        return "Total Lunar Eclipse"
    if retflag & ECL_PARTIAL:
        return "Partial Lunar Eclipse"
    if retflag & ECL_PENUMBRAL:
        return "Penumbral Lunar Eclipse"
    return "Lunar Eclipse"


def configure_ephemeris_path() -> int:
    """
    Configure Swiss Ephemeris path and base flags for calculations.

    The path is (re-)applied on every call: ``set_ephe_path`` is cheap and
    idempotent on both backends, while a once-only cache would silently
    leave the path unset after any session reset elsewhere in the process
    (``reset_session()``/``close()`` clear it), causing a fallback to
    default data discovery — or, on pyswisseph, to the low-precision
    Moshier ephemeris.

    Prefer ``kerykeion.ephemeris_backend.ephemeris_session`` for new code;
    it handles path setup, locking, and cleanup in one place.

    Returns:
        int: Base iflag (FLG_SWIEPH) to be used in ephe.calc_ut-style functions.
    """
    ephe.set_ephe_path(EPHE_DATA_PATH)
    return ephe.FLG_SWIEPH


def _extract_eclipse_result(result: object) -> Optional[tuple[int, float]]:
    """
    Extract (retflag, jd) from Swiss Ephemeris eclipse calculation result.

    Swiss Ephemeris eclipse functions return (retflag, tret) or (retflag, tret, attr)
    where tret is a tuple of floats with tret[0] being the Julian Day of the eclipse.

    Args:
        result: Raw result from ephe.sol_eclipse_when_glob or ephe.lun_eclipse_when.

    Returns:
        Optional[tuple[int, float]]: (retflag, eclipse_jd) or None if extraction fails.
    """
    if not (isinstance(result, tuple) and len(result) >= 2):
        return None

    retflag = result[0]
    tret = result[1]

    if not tret or not isinstance(tret[0], (float, int)):
        return None

    return retflag, float(tret[0])


def compute_next_solar_eclipse_jd(jd_start: float) -> Optional[tuple[int, float]]:
    """
    Compute the next global solar eclipse after the given Julian day.

    Uses Swiss Ephemeris to find the next solar eclipse visible anywhere on Earth.

    Args:
        jd_start: Starting Julian Day in Universal Time (UT).

    Returns:
        Optional[tuple[int, float]]: (retflag, eclipse_jd) where:
            - retflag: Eclipse type flags (e.g. SE_ECL_TOTAL, SE_ECL_PARTIAL)
            - eclipse_jd: Julian Day of maximum eclipse in UT
            Returns None if calculation fails or no eclipse found.

    Examples:
        >>> from kerykeion.utilities import datetime_to_julian
        >>> jd = datetime_to_julian(datetime(2025, 1, 1, tzinfo=timezone.utc))
        >>> result = compute_next_solar_eclipse_jd(jd)
        >>> if result:
        ...     retflag, eclipse_jd = result
        ...     eclipse_type = describe_solar_eclipse_type(retflag)
    """
    try:
        iflag = configure_ephemeris_path()
        result = ephe.sol_eclipse_when_glob(jd_start, iflag)
    except _BACKEND_ERRORS as exc:
        # Expected error: ephemeris data unavailable, date out of range, etc.
        logger.debug("Solar eclipse calculation failed (expected): %s", exc)
        return None
    except (AttributeError, TypeError) as exc:  # pragma: no cover
        # Unexpected error: potential bug in code or swisseph library issue
        logger.error("Unexpected error in solar eclipse calculation: %s", exc, exc_info=True)
        return None

    return _extract_eclipse_result(result)


def compute_next_lunar_eclipse_jd(jd_start: float) -> Optional[tuple[int, float]]:
    """
    Compute the next global lunar eclipse after the given Julian day.

    Uses Swiss Ephemeris to find the next lunar eclipse visible anywhere on Earth.

    Args:
        jd_start: Starting Julian Day in Universal Time (UT).

    Returns:
        Optional[tuple[int, float]]: (retflag, eclipse_jd) where:
            - retflag: Eclipse type flags (e.g. SE_ECL_TOTAL, SE_ECL_PARTIAL)
            - eclipse_jd: Julian Day of maximum eclipse in UT
            Returns None if calculation fails or no eclipse found.

    Examples:
        >>> from kerykeion.utilities import datetime_to_julian
        >>> jd = datetime_to_julian(datetime(2025, 1, 1, tzinfo=timezone.utc))
        >>> result = compute_next_lunar_eclipse_jd(jd)
        >>> if result:
        ...     retflag, eclipse_jd = result
        ...     eclipse_type = describe_lunar_eclipse_type(retflag)
    """
    try:
        iflag = configure_ephemeris_path()
        result = ephe.lun_eclipse_when(jd_start, iflag)
    except _BACKEND_ERRORS as exc:
        # Expected error: ephemeris data unavailable, date out of range, etc.
        logger.debug("Lunar eclipse calculation failed (expected): %s", exc)
        return None
    except (AttributeError, TypeError) as exc:  # pragma: no cover
        # Unexpected error: potential bug in code or swisseph library issue
        logger.error("Unexpected error in lunar eclipse calculation: %s", exc, exc_info=True)
        return None

    return _extract_eclipse_result(result)


def _extract_event_time(result: object) -> Optional[float]:
    """
    Extract the primary event time (JD) from an `ephe.rise_trans` result.

    The backend returns:

        (res, tret)

    where:
        - res: integer status (0 = event found, -2 = circumpolar, etc.)
        - tret: tuple of 10 floats, with tret[0] = JD of the event.

    Module-level rather than nested so the rise/set and transit helpers share
    one reading of that contract: they must agree on what "no event" means, and
    two copies would be free to drift apart.
    """
    if not isinstance(result, tuple) or not result:
        return None

    if len(result) < 2:
        return None

    res, tret = result[0], result[1]

    # We only accept res == 0 (event found).
    if not isinstance(res, int) or res != 0:
        return None

    if not isinstance(tret, (list, tuple)) or not tret:
        return None

    if not isinstance(tret[0], (float, int)):
        return None

    return float(tret[0])


def compute_sun_transit_ephe(
    jd_start: float,
    latitude: float,
    longitude: float,
) -> Optional[float]:
    """
    Compute the Sun's next upper meridian transit — true local noon.

    This is the instant the Sun crosses the observer's meridian, i.e. the moment
    it is highest in the sky. It is NOT the midpoint between sunrise and sunset:
    the two coincide only when the declination is stationary. Away from the
    solstices the midpoint drifts, and it drifts further the higher the latitude
    (measured against this function: +21 s at Rome on the equinox, +34 s at
    Ushuaia, +62 s at Reykjavik) — while at a longitude far from its timezone
    the midpoint can land on the wrong civil day altogether.

    A transit is a pure hour-angle search, so unlike rise/set it has no horizon,
    no disc and no refraction: `atpress`/`attemp` are accepted by the backend and
    ignored on this path, and the geocentric place is the correct one (diurnal
    parallax displaces a body in altitude only, leaving the hour angle intact).
    It also exists on days when rise and set do not — the Sun still culminates
    during polar night — which is why the caller must not gate it on them.

    Args:
        jd_start: Julian Day (UT) to search forward from, normally local midnight.
        latitude: Observer latitude in degrees.
        longitude: Observer longitude in degrees.

    Returns:
        The transit instant as a Julian Day, or ``None`` if the backend could not
        produce one.
    """
    try:
        iflag = configure_ephemeris_path()
        geopos = (float(longitude), float(latitude), 0.0)
        CALC_MTRANSIT = getattr(ephe, "CALC_MTRANSIT", getattr(ephe, "SE_CALC_MTRANSIT", 4))

        result = ephe.rise_trans(
            jd_start,
            ephe.SUN,
            CALC_MTRANSIT,
            geopos,
            atpress=0.0,
            attemp=0.0,
            flags=iflag,
        )
        return _extract_event_time(result)

    except _BACKEND_ERRORS as exc:
        logger.debug("Sun transit calculation failed: %s", exc)
        return None
    except (AttributeError, TypeError, IndexError, ValueError) as exc:  # pragma: no cover
        logger.error("Unexpected error in Sun transit calculation: %s", exc, exc_info=True)
        return None


def compute_sun_rise_set_ephe(
    jd_midnight: float,
    latitude: float,
    longitude: float,
) -> tuple[Optional[float], Optional[float]]:
    """
    Compute precise sunrise and sunset times via the backend's `rise_trans`.

    This helper delegates the heavy lifting to the backend's dedicated
    rise/transit routines, avoiding any custom numerical search logic.

    The event is the apparent UPPER LIMB on the horizon under a standard
    atmosphere (1013.25 hPa, 15 degrees C), which leaves the Sun's geometric
    centre near -0.83 degrees. That is deliberately a different question from
    ``AstrologicalSubjectModel.is_diurnal``, which tests the geometric centre
    against the true horizon: within a few minutes of the event the two
    legitimately disagree, by 3.3 min at the equator and 10 min at 70 degrees.

    Args:
        jd_midnight: Julian Day at the start of the *local* civil day,
            expressed in UT (i.e. the Julian day of local midnight converted
            to UTC). The backend will search for events around this time.
        latitude: Observer latitude in degrees.
        longitude: Observer longitude in degrees.

    Returns:
        tuple[Optional[float], Optional[float]]: (sunrise_jd, sunset_jd)
            Returns None for each event that doesn't occur on this day (polar day/night).
    """
    try:
        # Ensure the ephemeris backend is configured (idempotent).
        iflag = configure_ephemeris_path()

        # Observer position: longitude, latitude, altitude (meters)
        geopos = (float(longitude), float(latitude), 0.0)

        # Standard meteorological conditions for atmospheric refraction
        atpress = STANDARD_ATMOSPHERIC_PRESSURE_HPA
        attemp = STANDARD_TEMPERATURE_CELSIUS

        # Compatibility shims for rise/set calculation flags
        CALC_RISE = getattr(ephe, "CALC_RISE", getattr(ephe, "SE_CALC_RISE", 1))
        CALC_SET = getattr(ephe, "CALC_SET", getattr(ephe, "SE_CALC_SET", 2))

        # Sunrise (next rise after jd_midnight)
        sunrise_result = ephe.rise_trans(
            jd_midnight,
            ephe.SUN,
            CALC_RISE,
            geopos,
            atpress=atpress,
            attemp=attemp,
            flags=iflag,
        )

        # Sunset (next set after jd_midnight)
        sunset_result = ephe.rise_trans(
            jd_midnight,
            ephe.SUN,
            CALC_SET,
            geopos,
            atpress=atpress,
            attemp=attemp,
            flags=iflag,
        )

        sunrise_jd = _extract_event_time(sunrise_result)
        sunset_jd = _extract_event_time(sunset_result)

        return sunrise_jd, sunset_jd

    except _BACKEND_ERRORS as exc:
        # Expected error: circumpolar conditions, ephemeris unavailable, etc.
        logger.debug("Sun rise/set calculation failed (expected for polar regions): %s", exc)
        return None, None
    except (AttributeError, TypeError, IndexError, ValueError) as exc:  # pragma: no cover
        # Unexpected error: potential bug in code
        logger.error("Unexpected error in Sun rise/set calculation: %s", exc, exc_info=True)
        return None, None


def compute_lunar_phase_jd(
    jd_start: float,
    target_angle: float,
    forward: bool = True,
) -> Optional[float]:
    """
    Compute exact Julian Day when Sun-Moon longitudinal angle reaches target value.

    Uses binary search with Swiss Ephemeris for maximum precision (~1 second),
    replacing the mean synodic month approximation. The bracketing walk covers
    up to ±31 days from jd_start, enough for any same-phase spacing.

    Args:
        jd_start: Starting Julian Day in Universal Time (UT).
        target_angle: Target Sun-Moon ecliptic longitudinal separation in degrees [0, 360).
            Common values:
                - 0° = New Moon (Sun and Moon aligned)
                - 90° = First Quarter (Moon 90° east of Sun)
                - 180° = Full Moon (Moon opposite Sun)
                - 270° = Last Quarter (Moon 90° west of Sun)
        forward: If True, find the first occurrence after jd_start; if False,
            find the most recent occurrence at or before jd_start.

    Returns:
        Julian Day (UT) when the phase angle is reached with ~1 second precision,
        or None if calculation fails or phase is not found within the ±31 day search window.

    Examples:
        >>> # Find next Full Moon after Jan 1, 2025
        >>> from kerykeion.utilities import datetime_to_julian, julian_to_datetime
        >>> jd = datetime_to_julian(datetime(2025, 1, 1, tzinfo=timezone.utc))
        >>> full_moon_jd = compute_lunar_phase_jd(jd, 180.0, forward=True)
        >>> if full_moon_jd:
        ...     full_moon_dt = julian_to_datetime(full_moon_jd)
        ...     print(f"Next Full Moon: {full_moon_dt}")
    """
    try:
        configure_ephemeris_path()
        iflag = ephe.FLG_SWIEPH

        # Normalize target angle to [0, 360)
        target_angle = target_angle % 360.0

        # Search range: the daily bracketing walk below covers search_range + 1
        # = 31 days, enough for any spacing between consecutive same-phase
        # instants: new/full repeat within ~29.27-29.83 days, and quarter
        # phases stretch slightly wider (measured max 29.93 days over
        # 1990-2045) because the lunar anomaly affects them more strongly.
        # Mean synodic month: 29.530588853 days (Chapront ELP 2000-82B)
        # Source: https://eclipse.gsfc.nasa.gov/SEhelp/moonorbit.html
        search_range = 30.0

        def _signed_diff(jd: float) -> float:
            # Sun-Moon separation minus target, normalized to [-180, 180) so the
            # sought instant is an upward zero crossing (the separation grows
            # monotonically at ~12.2°/day).
            sun_pos = ephe.calc_ut(jd, ephe.SUN, iflag)[0]
            moon_pos = ephe.calc_ut(jd, ephe.MOON, iflag)[0]
            angle = (float(moon_pos[0]) - float(sun_pos[0])) % 360.0
            return wrap_180(angle - target_angle)

        # The normalized diff is a sawtooth: it rises through zero exactly at
        # the sought instants and jumps from +180 to -180 once per synodic
        # month. Plain bisection over a 30-day window is unreliable on such a
        # shape — depending on where the wrap falls it can converge on the
        # wrap itself (the opposite phase) or collapse onto a window edge.
        # So first bracket the nearest genuine crossing in the requested
        # direction with daily samples (a real crossing is a ~12° rise
        # between samples, unlike the ~360° jump at the wrap), then bisect
        # inside that one-day bracket.
        step = 1.0 if forward else -1.0
        prev_jd = jd_start
        prev_diff = _signed_diff(prev_jd)
        bracket = None
        for day in range(1, int(search_range) + 2):
            cur_jd = jd_start + step * float(day)
            cur_diff = _signed_diff(cur_jd)
            earlier_diff, later_diff = (prev_diff, cur_diff) if forward else (cur_diff, prev_diff)
            if earlier_diff < 0.0 <= later_diff:
                bracket = (min(prev_jd, cur_jd), max(prev_jd, cur_jd))
                break
            prev_jd, prev_diff = cur_jd, cur_diff
        if bracket is None:
            return None
        jd_min, jd_max = bracket

        # Binary search convergence criteria:
        # - Tolerance: 1 second = 1/86400 day (sufficient for astronomical applications)
        # - Max iterations: 50 (sufficient for 30-day range with binary halving)
        #   After 50 iterations: 30/(2^50) ≈ 2.7e-14 days ≈ 0.002 microseconds
        tolerance = 1.0 / 86400.0
        max_iterations = 50

        for _ in range(max_iterations):
            jd_mid = (jd_min + jd_max) / 2.0
            diff = _signed_diff(jd_mid)

            # The target instant is an upward zero crossing of diff: below the
            # target → it lies later, at/above → it lies at or earlier. The
            # backward case was bracketed above, so the same rule applies.
            if diff < 0:
                jd_min = jd_mid
            else:
                jd_max = jd_mid

            # Check if range is small enough
            if abs(jd_max - jd_min) < tolerance:
                return jd_mid

        # Fallback: return best estimate
        return (jd_min + jd_max) / 2.0

    except _BACKEND_ERRORS as exc:
        # Expected error: ephemeris data unavailable, date out of range, etc.
        logger.debug("Lunar phase calculation failed (expected): %s", exc)
        return None
    except (AttributeError, TypeError, IndexError) as exc:  # pragma: no cover
        # Unexpected error: potential bug in code
        logger.error("Unexpected error in lunar phase calculation: %s", exc, exc_info=True)
        return None


def greenwich_mean_sidereal_time(jd_ut: float) -> float:
    """
    Compute Greenwich Mean Sidereal Time in hours.
    """
    T = (jd_ut - 2451545.0) / 36525.0
    gmst_deg = 280.46061837 + 360.98564736629 * (jd_ut - 2451545.0) + 0.000387933 * (T**2) - (T**3) / 38710000.0
    gmst_hours = (gmst_deg % 360.0) / 15.0
    return gmst_hours


def equatorial_to_horizontal(
    ra_deg: float,
    dec_deg: float,
    jd_ut: float,
    latitude: float,
    longitude: float,
) -> tuple[float, float]:
    """
    Convert equatorial coordinates (RA, Dec) to horizontal coordinates (alt, az).

    Uses standard astronomical formulas for coordinate transformation based on
    the observer's location and the local sidereal time.

    Args:
        ra_deg: Right ascension in degrees.
        dec_deg: Declination in degrees.
        jd_ut: Julian Day in UT.
        latitude: Observer latitude in degrees.
        longitude: Observer longitude in degrees.

    Returns:
        tuple[float, float]: (altitude_degrees, azimuth_degrees).
    """
    # Convert RA to hours and angles to radians for spherical trigonometry
    ra_hours = ra_deg / 15.0
    dec_rad = math.radians(dec_deg)
    lat_rad = math.radians(latitude)

    gmst_hours = greenwich_mean_sidereal_time(jd_ut)
    # Local Sidereal Time = GMST + longitude correction
    lst_hours = (gmst_hours + longitude / 15.0) % 24.0

    # Hour Angle = LST - RA (measures time since object crossed meridian)
    H_hours = (lst_hours - ra_hours) % 24.0
    if H_hours > 12.0:
        H_hours -= 24.0
    H_rad = math.radians(H_hours * 15.0)

    # Altitude calculation using spherical trigonometry
    sin_alt = math.sin(dec_rad) * math.sin(lat_rad) + math.cos(dec_rad) * math.cos(lat_rad) * math.cos(H_rad)
    alt_rad = math.asin(max(-1.0, min(1.0, sin_alt)))  # Clamp to avoid numerical errors
    alt_deg = math.degrees(alt_rad)

    cos_alt = math.cos(alt_rad)
    if abs(cos_alt) < 1e-9:
        # Object is at zenith/nadir; azimuth is undefined, arbitrarily set to 0
        return alt_deg, 0.0

    # Azimuth calculation (0° = North, 90° = East, 180° = South, 270° = West)
    sin_az = -math.cos(dec_rad) * math.sin(H_rad) / cos_alt
    cos_az = (math.sin(dec_rad) - math.sin(alt_rad) * math.sin(lat_rad)) / (cos_alt * math.cos(lat_rad))

    az_rad = math.atan2(sin_az, cos_az)
    az_deg = (math.degrees(az_rad) + 360.0) % 360.0  # Normalize to [0, 360)

    return alt_deg, az_deg


def compute_sun_position(
    jd_ut: float,
    latitude: float,
    longitude: float,
) -> tuple[Optional[float], Optional[float], Optional[float]]:
    """
    Compute apparent Sun altitude, azimuth and distance using Swiss Ephemeris.

    Returns:
        tuple[Optional[float], Optional[float], Optional[float]]:
            (altitude_deg, azimuth_deg, distance_km)
    """
    try:
        configure_ephemeris_path()
        iflag = ephe.FLG_SWIEPH | ephe.FLG_SPEED
        sun_calc = ephe.calc_ut(jd_ut, ephe.SUN, iflag)[0]
        distance_km = float(sun_calc[2]) * AU_KM

        sun_eq = ephe.calc_ut(jd_ut, ephe.SUN, iflag | ephe.FLG_EQUATORIAL)[0]
        ra_deg = float(sun_eq[0])
        dec_deg = float(sun_eq[1])

        altitude, azimuth = equatorial_to_horizontal(ra_deg, dec_deg, jd_ut, latitude, longitude)
    except _BACKEND_ERRORS as exc:
        # Expected error: ephemeris data unavailable, date out of range, etc.
        logger.debug("Sun position calculation failed (expected): %s", exc)
        return None, None, None
    except (AttributeError, TypeError, IndexError) as exc:  # pragma: no cover
        # Unexpected error: potential bug in code
        logger.error("Unexpected error in Sun position calculation: %s", exc, exc_info=True)
        return None, None, None

    return altitude, azimuth, distance_km


__all__ = [
    "safe_parse_iso_datetime",
    "describe_solar_eclipse_type",
    "describe_lunar_eclipse_type",
    "configure_ephemeris_path",
    "compute_next_solar_eclipse_jd",
    "compute_next_lunar_eclipse_jd",
    "compute_sun_rise_set_ephe",
    "compute_sun_transit_ephe",
    "compute_lunar_phase_jd",
    "greenwich_mean_sidereal_time",
    "equatorial_to_horizontal",
    "compute_sun_position",
]
