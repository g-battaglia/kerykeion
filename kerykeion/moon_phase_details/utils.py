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
from pathlib import Path
from typing import Optional, Tuple
import swisseph as swe

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Swiss Ephemeris compatibility shims and constants
# ---------------------------------------------------------------------------

# Different swisseph builds expose eclipse flags with or without the SE_ prefix.
ECL_TOTAL = getattr(swe, "SE_ECL_TOTAL", getattr(swe, "ECL_TOTAL", 0))
ECL_ANNULAR_TOTAL = getattr(swe, "SE_ECL_ANNULAR_TOTAL", getattr(swe, "ECL_ANNULAR_TOTAL", 0))
ECL_ANNULAR = getattr(swe, "SE_ECL_ANNULAR", getattr(swe, "ECL_ANNULAR", 0))
ECL_PARTIAL = getattr(swe, "SE_ECL_PARTIAL", getattr(swe, "ECL_PARTIAL", 0))
ECL_PENUMBRAL = getattr(swe, "SE_ECL_PENUMBRAL", getattr(swe, "ECL_PENUMBRAL", 0))

# Distance unit conversion: Astronomical Unit to kilometers.
# IAU 2012 nominal value: 1 AU = 149,597,870.700 km exactly
# Source: https://www.iau.org/static/resolutions/IAU2012_English.pdf
AU_KM = getattr(swe, "AUNIT", 149597870.7)

# Standard meteorological conditions at sea level for atmospheric refraction calculations
# Used by Swiss Ephemeris rise/set routines to compute apparent horizon
# Source: Standard atmosphere (ISO 2533:1975)
STANDARD_ATMOSPHERIC_PRESSURE_HPA = 1013.25  # hectopascals (sea level)
STANDARD_TEMPERATURE_CELSIUS = 15.0  # degrees Celsius

# Global cache for ephemeris configuration
_EPHEMERIS_CONFIG = None


def safe_parse_iso_datetime(value: Optional[str]) -> datetime:
    """
    Parse an ISO formatted datetime string into an aware UTC datetime.

    This helper is defensive:
        - Accepts both standard ISO strings and those ending with 'Z'
        - Treats naive datetimes as UTC
        - Falls back to the current UTC time if parsing fails
    """
    if not value:
        logger.warning("safe_parse_iso_datetime received empty value; using current UTC time.")
        return datetime.now(timezone.utc)

    try:
        dt = datetime.fromisoformat(value)
    except ValueError:
        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except Exception as exc:
            logger.warning(
                "safe_parse_iso_datetime failed to parse value %r (%s); using current UTC time.",
                value,
                exc,
            )
            return datetime.now(timezone.utc)

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

    This function is idempotent - it sets the ephemeris path only once
    on first call and caches the result, improving performance for
    subsequent calls.

    Returns:
        int: Base iflag (FLG_SWIEPH) to be used in swe.calc_ut-style functions.
    """
    global _EPHEMERIS_CONFIG
    if _EPHEMERIS_CONFIG is None:
        ephe_path = str(Path(__file__).parents[1].absolute() / "sweph")
        swe.set_ephe_path(ephe_path)
        _EPHEMERIS_CONFIG = swe.FLG_SWIEPH
    return _EPHEMERIS_CONFIG


def _extract_eclipse_result(result: object) -> Optional[Tuple[int, float]]:
    """
    Extract (retflag, jd) from Swiss Ephemeris eclipse calculation result.
    
    Swiss Ephemeris eclipse functions return (retflag, tret) or (retflag, tret, attr)
    where tret is a tuple of floats with tret[0] being the Julian Day of the eclipse.
    
    Args:
        result: Raw result from swe.sol_eclipse_when_glob or swe.lun_eclipse_when.
    
    Returns:
        Optional[Tuple[int, float]]: (retflag, eclipse_jd) or None if extraction fails.
    """
    if not (isinstance(result, tuple) and len(result) >= 2):
        return None
    
    retflag = result[0]
    tret = result[1]
    
    if not tret or not isinstance(tret[0], (float, int)):
        return None
    
    return retflag, float(tret[0])


def compute_next_solar_eclipse_jd(jd_start: float) -> Optional[Tuple[int, float]]:
    """
    Compute the next global solar eclipse after the given Julian day.
    
    Uses Swiss Ephemeris to find the next solar eclipse visible anywhere on Earth.
    
    Args:
        jd_start: Starting Julian Day in Universal Time (UT).
    
    Returns:
        Optional[Tuple[int, float]]: (retflag, eclipse_jd) where:
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
        result = swe.sol_eclipse_when_glob(jd_start, iflag)
    except RuntimeError as exc:
        # Expected error: ephemeris data unavailable, date out of range, etc.
        logger.debug("Solar eclipse calculation failed (expected): %s", exc)
        return None
    except (AttributeError, TypeError) as exc:  # pragma: no cover
        # Unexpected error: potential bug in code or swisseph library issue
        logger.error("Unexpected error in solar eclipse calculation: %s", exc, exc_info=True)
        return None

    return _extract_eclipse_result(result)


def compute_next_lunar_eclipse_jd(jd_start: float) -> Optional[Tuple[int, float]]:
    """
    Compute the next global lunar eclipse after the given Julian day.
    
    Uses Swiss Ephemeris to find the next lunar eclipse visible anywhere on Earth.
    
    Args:
        jd_start: Starting Julian Day in Universal Time (UT).
    
    Returns:
        Optional[Tuple[int, float]]: (retflag, eclipse_jd) where:
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
        result = swe.lun_eclipse_when(jd_start, iflag)
    except RuntimeError as exc:
        # Expected error: ephemeris data unavailable, date out of range, etc.
        logger.debug("Lunar eclipse calculation failed (expected): %s", exc)
        return None
    except (AttributeError, TypeError) as exc:  # pragma: no cover
        # Unexpected error: potential bug in code or swisseph library issue
        logger.error("Unexpected error in lunar eclipse calculation: %s", exc, exc_info=True)
        return None

    return _extract_eclipse_result(result)


def compute_sun_rise_set_swe(
    jd_midnight: float,
    latitude: float,
    longitude: float,
) -> Tuple[Optional[float], Optional[float]]:
    """
    Compute precise sunrise and sunset times using Swiss Ephemeris `swe.rise_trans`.

    This helper delegates the heavy lifting to Swiss Ephemeris' dedicated
    rise/transit routines, avoiding any custom numerical search logic.

    Args:
        jd_midnight: Julian Day at the start of the *local* civil day,
            expressed in UT (i.e. the Julian day of local midnight converted
            to UTC). Swiss Ephemeris will search for events around this time.
        latitude: Observer latitude in degrees.
        longitude: Observer longitude in degrees.

    Returns:
        Tuple[Optional[float], Optional[float]]: (sunrise_jd, sunset_jd)
            Returns None for each event that doesn't occur on this day (polar day/night).
    """
    try:
        # Ensure Swiss Ephemeris is configured (idempotent).
        iflag = configure_ephemeris_path()

        # Observer position: longitude, latitude, altitude (meters)
        geopos = (float(longitude), float(latitude), 0.0)

        # Standard meteorological conditions for atmospheric refraction
        atpress = STANDARD_ATMOSPHERIC_PRESSURE_HPA
        attemp = STANDARD_TEMPERATURE_CELSIUS

        # Compatibility shims for rise/set calculation flags
        CALC_RISE = getattr(swe, "CALC_RISE", getattr(swe, "SE_CALC_RISE", 1))
        CALC_SET = getattr(swe, "CALC_SET", getattr(swe, "SE_CALC_SET", 2))

        def _extract_event_time(result: object) -> Optional[float]:
            """
            Extract the primary event time (JD) from `swe.rise_trans` result.

            According to the Python wrapper documentation, the result is:

                (res, tret)

            where:
                - res: integer status (0 = event found, -2 = circumpolar, etc.)
                - tret: tuple of 10 floats, with tret[0] = JD of the event.
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

        # Sunrise (next rise after jd_midnight)
        sunrise_result = swe.rise_trans(
            jd_midnight,
            swe.SUN,
            CALC_RISE,
            geopos,
            atpress=atpress,
            attemp=attemp,
            flags=iflag,
        )

        # Sunset (next set after jd_midnight)
        sunset_result = swe.rise_trans(
            jd_midnight,
            swe.SUN,
            CALC_SET,
            geopos,
            atpress=atpress,
            attemp=attemp,
            flags=iflag,
        )

        sunrise_jd = _extract_event_time(sunrise_result)
        sunset_jd = _extract_event_time(sunset_result)

        return sunrise_jd, sunset_jd

    except RuntimeError as exc:
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
    replacing the mean synodic month approximation. The search is constrained
    to ±30 days from jd_start to ensure convergence.

    Args:
        jd_start: Starting Julian Day in Universal Time (UT).
        target_angle: Target Sun-Moon ecliptic longitudinal separation in degrees [0, 360).
            Common values:
                - 0° = New Moon (Sun and Moon aligned)
                - 90° = First Quarter (Moon 90° east of Sun)
                - 180° = Full Moon (Moon opposite Sun)
                - 270° = Last Quarter (Moon 90° west of Sun)
        forward: If True, search forward in time; if False, search backward.

    Returns:
        Julian Day (UT) when the phase angle is reached with ~1 second precision,
        or None if calculation fails or phase is not found within ±30 day search window.

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
        iflag = swe.FLG_SWIEPH

        # Normalize target angle to [0, 360)
        target_angle = target_angle % 360.0

        # Search range: ±30 days is sufficient to find any lunar phase.
        # Synodic month varies between ~29.27 and ~29.83 days (extremes).
        # Mean synodic month: 29.530588853 days (Chapront ELP 2000-82B)
        # Source: https://eclipse.gsfc.nasa.gov/SEhelp/moonorbit.html
        search_range = 30.0

        if forward:
            jd_min = jd_start
            jd_max = jd_start + search_range
        else:
            jd_min = jd_start - search_range
            jd_max = jd_start

        # Binary search convergence criteria:
        # - Tolerance: 1 second = 1/86400 day (sufficient for astronomical applications)
        # - Max iterations: 50 (sufficient for 30-day range with binary halving)
        #   After 50 iterations: 30/(2^50) ≈ 2.7e-14 days ≈ 0.002 microseconds
        tolerance = 1.0 / 86400.0
        max_iterations = 50

        for _ in range(max_iterations):
            jd_mid = (jd_min + jd_max) / 2.0

            # Get Sun and Moon positions
            sun_pos = swe.calc_ut(jd_mid, swe.SUN, iflag)[0]
            moon_pos = swe.calc_ut(jd_mid, swe.MOON, iflag)[0]

            # Calculate Sun-Moon angle
            sun_lon = float(sun_pos[0])
            moon_lon = float(moon_pos[0])
            angle = (moon_lon - sun_lon) % 360.0

            # Normalize angular difference to [-180, 180) to handle angle wrapping.
            # Example: if angle=10° and target=350°, diff should be 20° (not -340°)
            diff = (angle - target_angle + 180.0) % 360.0 - 180.0

            # Binary search logic:
            # - Forward search: if Moon hasn't reached target (diff < 0), advance time
            # - Backward search: if Moon is past target (diff > 0), go back in time
            if (forward and diff < 0) or (not forward and diff > 0):
                jd_min = jd_mid  # Target phase occurs later in time
            else:
                jd_max = jd_mid  # Target phase occurs earlier in time

            # Check if range is small enough
            if abs(jd_max - jd_min) < tolerance:
                return jd_mid

        # Fallback: return best estimate
        return (jd_min + jd_max) / 2.0

    except RuntimeError as exc:
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
    gmst_deg = (
        280.46061837
        + 360.98564736629 * (jd_ut - 2451545.0)
        + 0.000387933 * (T ** 2)
        - (T ** 3) / 38710000.0
    )
    gmst_hours = (gmst_deg % 360.0) / 15.0
    return gmst_hours


def equatorial_to_horizontal(
    ra_deg: float,
    dec_deg: float,
    jd_ut: float,
    latitude: float,
    longitude: float,
) -> Tuple[float, float]:
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
        Tuple[float, float]: (altitude_degrees, azimuth_degrees).
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
) -> Tuple[Optional[float], Optional[float], Optional[float]]:
    """
    Compute apparent Sun altitude, azimuth and distance using Swiss Ephemeris.

    Returns:
        Tuple[Optional[float], Optional[float], Optional[float]]:
            (altitude_deg, azimuth_deg, distance_km)
    """
    try:
        configure_ephemeris_path()
        iflag = swe.FLG_SWIEPH | swe.FLG_SPEED
        sun_calc = swe.calc_ut(jd_ut, swe.SUN, iflag)[0]
        distance_km = float(sun_calc[2]) * AU_KM

        sun_eq = swe.calc_ut(jd_ut, swe.SUN, iflag | swe.FLG_EQUATORIAL)[0]
        ra_deg = float(sun_eq[0])
        dec_deg = float(sun_eq[1])

        altitude, azimuth = equatorial_to_horizontal(ra_deg, dec_deg, jd_ut, latitude, longitude)
    except RuntimeError as exc:
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
    "compute_sun_rise_set_swe",
    "compute_lunar_phase_jd",
    "greenwich_mean_sidereal_time",
    "equatorial_to_horizontal",
    "compute_sun_position",
]
