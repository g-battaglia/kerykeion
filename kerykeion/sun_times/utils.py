# -*- coding: utf-8 -*-
"""
Low-level sun-event helpers for :class:`SunTimesFactory`.

The heavy astronomical work — locating sunrise and sunset with atmospheric
refraction — is delegated to the well-tested
:func:`kerykeion.moon_phase_details.utils.compute_sun_rise_set_swe`, which calls
the active ephemeris backend's ``rise_trans`` routine. This module adds the thin
layer on top: timezone/Julian-Day bookkeeping, solar noon, day length, and the
polar day / polar night discriminator. No full astrological subject is built, so
the computation is cheap (two ``rise_trans`` calls plus one position lookup).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Optional

import pytz
from pytz.exceptions import AmbiguousTimeError, NonExistentTimeError

from kerykeion.ephemeris_backend import swe
from kerykeion.moon_phase_details.utils import (
    compute_sun_rise_set_swe,
    configure_ephemeris_path,
)
from kerykeion.schemas.kerykeion_exception import KerykeionException
from kerykeion.utilities import datetime_to_julian, julian_to_datetime


_APPARENT_UPPER_LIMB_HORIZON_DEGREES = -0.833


@dataclass(frozen=True)
class SunEvents:
    """Raw sun-event results for a single civil day at one location.

    Instants are timezone-aware UTC ``datetime`` objects when present. On polar
    and boundary days, sunrise or sunset can be missing independently; derived
    solar noon and day length require a sunrise paired with a later sunset.
    """

    sunrise: Optional[datetime]
    sunset: Optional[datetime]
    solar_noon: Optional[datetime]
    day_length: Optional[timedelta]
    is_polar_day: bool
    is_polar_night: bool


def resolve_timezone(tz_str: str) -> pytz.BaseTzInfo:
    """Resolve an IANA timezone string, raising ``KerykeionException`` if invalid.

    Args:
        tz_str: IANA timezone identifier (e.g. ``"Europe/Rome"``).

    Returns:
        The corresponding ``pytz`` timezone object.

    Raises:
        KerykeionException: If ``tz_str`` is not a known IANA timezone.
    """
    try:
        return pytz.timezone(tz_str)
    except pytz.UnknownTimeZoneError as exc:
        raise KerykeionException(f"Unknown timezone: {tz_str!r}") from exc


def localize_datetime(
    year: int,
    month: int,
    day: int,
    hour: int = 0,
    minute: int = 0,
    second: int = 0,
    *,
    tz: pytz.BaseTzInfo,
) -> datetime:
    """Build a timezone-aware local ``datetime``, validating the inputs.

    These timing factories are anchored to civil (IANA) timezones, so they operate
    on the years Python's ``datetime`` can represent (1-9999 CE). Out-of-range
    years and impossible dates (e.g. 30 February) are reported as a clean
    ``KerykeionException`` rather than a raw ``ValueError``.

    Raises:
        KerykeionException: If the date/time is invalid or the year is unsupported.
    """
    try:
        naive = datetime(int(year), int(month), int(day), int(hour), int(minute), int(second))
    except (ValueError, OverflowError) as exc:
        raise KerykeionException(
            f"Invalid or unsupported date/time ({year:04d}-{month:02d}-{day:02d} "
            f"{hour:02d}:{minute:02d}): {exc}. Supported civil years are 1-9999 CE."
        ) from exc
    try:
        return tz.localize(naive, is_dst=None)
    except (AmbiguousTimeError, NonExistentTimeError) as exc:
        raise KerykeionException(f"Invalid or ambiguous local time {naive!s} in timezone {tz.zone!r}: {exc}") from exc


def local_midnight_julian_day(year: int, month: int, day: int, tz: pytz.BaseTzInfo) -> float:
    """Julian Day (UT) of local civil midnight for the given date and timezone.

    ``rise_trans`` searches for the next rise/set *after* this instant, so seeding
    it with local midnight yields that civil day's sunrise and sunset.

    Note:
        ``datetime_to_julian`` reads the datetime's wall-clock fields and ignores
        ``tzinfo``, so the local midnight is converted to UTC first.
    """
    utc_midnight = localize_datetime(year, month, day, tz=tz).astimezone(pytz.utc)
    return datetime_to_julian(utc_midnight)


def julian_day_to_utc(jd: float) -> datetime:
    """Convert a Julian Day (UT) to a timezone-aware UTC ``datetime``."""
    return julian_to_datetime(jd).replace(tzinfo=timezone.utc)


def _polar_state(jd_noon: float, latitude: float) -> tuple[bool, bool]:
    """Classify a no-rise/no-set day as polar day or polar night.

    Uses the same apparent upper-limb horizon convention as Swiss Ephemeris
    rise/set searches. Refraction and the Sun's semidiameter put the apparent
    sunrise/sunset threshold near -0.833 degrees for the Sun's center.

    Args:
        jd_noon: Julian Day (UT) near local solar noon — used to read the Sun's
            declination for the day.
        latitude: Observer latitude in degrees.

    Returns:
        ``(is_polar_day, is_polar_night)``.
    """
    iflag = configure_ephemeris_path()
    # Equatorial coordinates: [right_ascension, declination, distance, ...].
    declination = swe.calc_ut(jd_noon, swe.SUN, iflag | swe.FLG_EQUATORIAL)[0][1]
    horizon = math.radians(_APPARENT_UPPER_LIMB_HORIZON_DEGREES)
    lat = math.radians(latitude)
    decl = math.radians(declination)
    denominator = math.cos(lat) * math.cos(decl)
    if abs(denominator) < 1e-12:
        return latitude * declination > 0, latitude * declination < 0

    cos_hour_angle = (math.sin(horizon) - math.sin(lat) * math.sin(decl)) / denominator
    return cos_hour_angle < -1.0, cos_hour_angle > 1.0


def compute_sun_events(
    year: int, month: int, day: int, latitude: float, longitude: float, tz: pytz.BaseTzInfo
) -> SunEvents:
    """Compute sunrise, sunset, solar noon, day length and polar flags.

    Args:
        year, month, day: Civil date in the supplied timezone.
        latitude: Observer latitude in degrees (north positive).
        longitude: Observer longitude in degrees (east positive).
        tz: Resolved ``pytz`` timezone the civil date is anchored to.

    Returns:
        A :class:`SunEvents` with timezone-aware UTC instants (or ``None`` on
        polar day/night, in which case the relevant flag is set).

    Raises:
        KerykeionException: If the backend cannot evaluate the Sun, or returns no
            rise/set while the geometry is not polar (e.g. a date/location outside
            the backend's supported rise/set range).
    """
    jd_midnight = local_midnight_julian_day(year, month, day, tz)
    try:
        next_day = date(year, month, day) + timedelta(days=1)
        jd_next_midnight = local_midnight_julian_day(next_day.year, next_day.month, next_day.day, tz)
    except OverflowError:
        # Last representable civil day: the exact next local midnight is unrepresentable.
        jd_next_midnight = jd_midnight + 1.0

    sunrise_jd, sunset_jd = compute_sun_rise_set_swe(jd_midnight, latitude, longitude)

    # rise_trans searches forward with no upper bound, so on polar-edge days it can
    # return the *next* civil day's rise/set. Discard anything at or past the next
    # local midnight before pairing a later sunset, so we never report another day's
    # sun times; a genuine polar day then falls through to the polar branch below.
    if sunrise_jd is not None and sunrise_jd >= jd_next_midnight:
        sunrise_jd = None
    if sunset_jd is not None and sunset_jd >= jd_next_midnight:
        sunset_jd = None

    if sunrise_jd is not None and sunset_jd is not None and sunset_jd <= sunrise_jd:
        _, paired_sunset_jd = compute_sun_rise_set_swe(sunrise_jd + 1e-6, latitude, longitude)
        sunset_jd = paired_sunset_jd if paired_sunset_jd is not None and paired_sunset_jd > sunrise_jd else None

    if sunrise_jd is None or sunset_jd is None:
        try:
            is_polar_day, is_polar_night = _polar_state(jd_midnight + 0.5, latitude)
        except Exception as exc:
            raise KerykeionException(
                f"The ephemeris backend failed to evaluate the Sun for {year:04d}-{month:02d}-{day:02d} "
                f"at latitude {latitude}: {exc}."
            ) from exc
        if sunrise_jd is None and sunset_jd is None and not (is_polar_day or is_polar_night):
            raise KerykeionException(
                f"The ephemeris backend returned no sunrise or sunset for {year:04d}-{month:02d}-{day:02d} "
                f"at ({latitude}, {longitude}) and the geometry is not polar; the date or location may be "
                f"outside the backend's supported rise/set range."
            )
        sunrise = julian_day_to_utc(sunrise_jd) if sunrise_jd is not None else None
        sunset = julian_day_to_utc(sunset_jd) if sunset_jd is not None else None
        return SunEvents(sunrise, sunset, None, None, is_polar_day, is_polar_night)

    sunrise = julian_day_to_utc(sunrise_jd)
    sunset = julian_day_to_utc(sunset_jd)
    day_length = sunset - sunrise
    solar_noon = sunrise + day_length / 2
    return SunEvents(sunrise, sunset, solar_noon, day_length, False, False)
