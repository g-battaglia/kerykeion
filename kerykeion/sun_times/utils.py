# -*- coding: utf-8 -*-
"""
Low-level sun-event helpers for :class:`SunTimesFactory`.

The heavy astronomical work — locating sunrise and sunset with atmospheric
refraction — is delegated to the well-tested
:func:`kerykeion.moon_phase_details.utils.compute_sun_rise_set_ephe`, which calls
the active ephemeris backend's ``rise_trans`` routine. This module adds the thin
layer on top: timezone/Julian-Day bookkeeping, solar noon, day length, the polar
day / polar night discriminator, and civil/nautical/astronomical twilight. No
full astrological subject is built, so the computation stays cheap: two
``rise_trans`` calls for sunrise/sunset (plus one position lookup) and up to six
more for the twilight crossings.
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Optional

import pytz
from pytz.exceptions import AmbiguousTimeError, NonExistentTimeError

from kerykeion.ephemeris_backend import ephemeris_session, ephe
from kerykeion.moon_phase_details.utils import (
    compute_sun_rise_set_ephe,
    configure_ephemeris_path,
)
from kerykeion.schemas.kerykeion_exception import KerykeionException
from kerykeion.utilities import datetime_to_julian, julian_to_datetime

logger = logging.getLogger(__name__)

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


@dataclass(frozen=True)
class TwilightEvents:
    """Civil/nautical/astronomical dawn and dusk for one civil day at a location.

    Each instant is a timezone-aware UTC ``datetime`` marking when the Sun's
    centre crosses the corresponding depression angle (-6 / -12 / -18 degrees) on
    the requested civil day, or ``None`` when that twilight does not occur — e.g.
    high-latitude summer where the Sun never sinks to -18 degrees, or polar day.
    Dawn is the morning (ascending) crossing, dusk the evening (descending) one.
    """

    civil_dawn: Optional[datetime]
    civil_dusk: Optional[datetime]
    nautical_dawn: Optional[datetime]
    nautical_dusk: Optional[datetime]
    astronomical_dawn: Optional[datetime]
    astronomical_dusk: Optional[datetime]


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
    except AmbiguousTimeError:
        # DST fall-back: the same wall-clock time exists twice. Default to the
        # standard-time (post-transition) interpretation so the caller always
        # gets a deterministic result without needing an extra parameter.
        return tz.localize(naive, is_dst=False)
    except NonExistentTimeError as exc:
        raise KerykeionException(f"Non-existent local time {naive!s} in timezone {tz.zone!r}: {exc}") from exc


def _localize_civil_midnight(year: int, month: int, day: int, tz: pytz.BaseTzInfo) -> datetime:
    """Timezone-aware first instant of a civil day, resolving DST gaps forward.

    Unlike :func:`localize_datetime` — used for *user-supplied* clock times, where
    a nonexistent time is a caller error worth raising — an internally constructed
    midnight that falls in a DST spring-forward gap (e.g. America/Sao_Paulo
    2018-11-04, America/Santiago 2022-09-11, Africa/Cairo 2023-04-28, where clocks
    jump straight from 00:00 to 01:00) is not an error: the civil day exists and
    simply begins at the end of the gap. Resolve such midnights forward to that
    first existing instant instead of rejecting a perfectly valid date.

    Raises:
        KerykeionException: If the date is invalid or the year is unsupported.
    """
    try:
        naive = datetime(int(year), int(month), int(day))
    except (ValueError, OverflowError) as exc:
        raise KerykeionException(
            f"Invalid or unsupported date ({year:04d}-{month:02d}-{day:02d}): {exc}. "
            f"Supported civil years are 1-9999 CE."
        ) from exc
    try:
        return tz.localize(naive, is_dst=None)
    except AmbiguousTimeError:
        # DST fall-back: midnight exists twice. Like localize_datetime, default to
        # the standard-time (post-transition) interpretation.
        return tz.localize(naive, is_dst=False)
    except NonExistentTimeError:
        # Spring-forward gap at midnight. Of the two possible interpretations the
        # later UTC instant is the one that lands *after* the gap (the pre-gap
        # offset overshoots forward when normalized), i.e. the day's real start.
        return max(
            tz.normalize(tz.localize(naive, is_dst=False)),
            tz.normalize(tz.localize(naive, is_dst=True)),
        )


def local_midnight_julian_day(year: int, month: int, day: int, tz: pytz.BaseTzInfo) -> float:
    """Julian Day (UT) of the start of the local civil day for a date and timezone.

    ``rise_trans`` searches for the next rise/set *after* this instant, so seeding
    it with local midnight yields that civil day's sunrise and sunset. When local
    midnight does not exist (a DST spring-forward gap at 00:00) the civil day's
    actual first instant — the end of the gap — is used instead.

    Note:
        The local midnight is converted to UTC before the Julian Day conversion.
    """
    utc_midnight = _localize_civil_midnight(year, month, day, tz).astimezone(pytz.utc)
    return datetime_to_julian(utc_midnight)


def julian_day_to_utc(jd: float) -> datetime:
    """Convert a Julian Day (UT) to a timezone-aware UTC ``datetime``."""
    return julian_to_datetime(jd).replace(tzinfo=timezone.utc)


def _civil_day_bounds(year: int, month: int, day: int, tz: pytz.BaseTzInfo) -> tuple[float, float]:
    """Julian Days (UT) of the local midnights opening and closing the civil day.

    Returns ``(jd_midnight, jd_next_midnight)``; the upper bound falls back to
    ``jd_midnight + 1`` when the following date overflows the supported range.
    """
    jd_midnight = local_midnight_julian_day(year, month, day, tz)
    try:
        next_day = date(year, month, day) + timedelta(days=1)
        jd_next_midnight = local_midnight_julian_day(next_day.year, next_day.month, next_day.day, tz)
    except OverflowError:
        jd_next_midnight = jd_midnight + 1.0
    return jd_midnight, jd_next_midnight


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

    Note:
        This function mutates global ephemeris state (``set_ephe_path``,
        ``calc_ut``). The caller must invoke it inside an
        :func:`~kerykeion.ephemeris_backend.ephemeris_session`.
    """
    iflag = configure_ephemeris_path()
    # Equatorial coordinates: [right_ascension, declination, distance, ...].
    declination = ephe.calc_ut(jd_noon, ephe.SUN, iflag | ephe.FLG_EQUATORIAL)[0][1]
    horizon = math.radians(_APPARENT_UPPER_LIMB_HORIZON_DEGREES)
    lat = math.radians(latitude)
    decl = math.radians(declination)
    denominator = math.cos(lat) * math.cos(decl)
    if abs(denominator) < 1e-12:
        # Exactly at a pole the Sun's altitude equals its declination all day:
        # compare against the apparent-horizon threshold (-0.833 deg), not the
        # sign of lat*decl — a declination in (-0.833, 0) at the North Pole is
        # still a 24h-visible Sun, not polar night.
        signed_altitude = declination if latitude > 0 else -declination
        above = signed_altitude > _APPARENT_UPPER_LIMB_HORIZON_DEGREES
        return above, not above

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
    jd_midnight, jd_next_midnight = _civil_day_bounds(year, month, day, tz)

    # The session serializes access to the process-global backend state and
    # resets it on exit without degrading the pinned calculation mode.
    with ephemeris_session():
        sunrise_jd, sunset_jd = compute_sun_rise_set_ephe(jd_midnight, latitude, longitude)
        # Whether a sunset exists at all (before civil-day bounding): distinguishes
        # "sunset falls just past local midnight" from "no sunset today" (polar).
        sunset_exists = sunset_jd is not None

        if sunrise_jd is not None and sunrise_jd >= jd_next_midnight:
            sunrise_jd = None
        if sunset_jd is not None and sunset_jd >= jd_next_midnight:
            sunset_jd = None

        if sunrise_jd is not None and sunset_jd is not None and sunset_jd <= sunrise_jd:
            # The only set inside the civil day precedes sunrise (the Sun was still
            # up at local midnight): pair sunrise with its actual following sunset.
            # This paired sunset is deliberately NOT re-bounded to the civil day, so
            # on high-latitude transition days it can fall on the next civil date and
            # make day_length exceed 24h — the correct continuous daylight span here.
            _, paired_sunset_jd = compute_sun_rise_set_ephe(sunrise_jd + 1e-6, latitude, longitude)
            sunset_jd = paired_sunset_jd if paired_sunset_jd is not None and paired_sunset_jd > sunrise_jd else None
        elif sunrise_jd is not None and sunset_jd is None and sunset_exists:
            # Mirror of the case above: a valid sunrise whose following sunset falls
            # just PAST local midnight (nulled by the civil-day bound). Without this
            # a high-latitude day with a real sunset after 00:00 returned
            # sunset/day_length/solar_noon = None with neither polar flag set — on a
            # day that is not polar. Recompute the sunset following sunrise.
            _, paired_sunset_jd = compute_sun_rise_set_ephe(sunrise_jd + 1e-6, latitude, longitude)
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


def _next_event_jd(
    jd_start: float, geopos: tuple[float, float, float], rsmi: int, iflag: int
) -> Optional[float]:
    """Julian Day (UT) of the next ``rise_trans`` event, or ``None`` if none found.

    Thin wrapper used for twilight crossings. The twilight bits make the backend
    search for the Sun's centre at a fixed geometric depression angle (no
    refraction), so no pressure/temperature is supplied. Only a clean ``res == 0``
    result is accepted; circumpolar / no-event results map to ``None``.

    Note:
        Mutates global ephemeris state via the backend; the caller must invoke it
        inside an :func:`~kerykeion.ephemeris_backend.ephemeris_session`.
    """
    try:
        result = ephe.rise_trans(jd_start, ephe.SUN, rsmi, geopos, atpress=0.0, attemp=0.0, flags=iflag)
    except RuntimeError as exc:
        # Expected at high latitudes: circumpolar at the depression angle (the Sun
        # never reaches it). A missing twilight crossing is normal, so degrade to None.
        logger.debug("Twilight rise/set unavailable (expected for polar geometry): %s", exc)
        return None
    except (AttributeError, TypeError, IndexError, ValueError, OverflowError) as exc:  # pragma: no cover
        logger.error("Unexpected error in twilight rise/set calculation: %s", exc, exc_info=True)
        return None
    if not isinstance(result, tuple) or len(result) < 2:
        return None
    res, tret = result[0], result[1]
    if not isinstance(res, int) or res != 0:
        return None
    if not isinstance(tret, (list, tuple)) or not tret or not isinstance(tret[0], (float, int)):
        return None
    return float(tret[0])


def compute_twilight_events(
    year: int, month: int, day: int, latitude: float, longitude: float, tz: pytz.BaseTzInfo
) -> TwilightEvents:
    """Compute civil, nautical and astronomical dawn/dusk for a civil day.

    Dawn is the morning crossing (Sun ascending to the depression angle) and dusk
    the evening crossing (descending past it), at -6 / -12 / -18 degrees. Dawn is
    sought from local midnight, dusk from local noon so it is the evening crossing;
    an evening dusk can therefore land in the small hours of the next civil date
    (as the paired sunset can). Each instant is a timezone-aware UTC ``datetime``,
    or ``None`` when that twilight does not occur (polar / high-latitude geometry).

    Args:
        year, month, day: Civil date in the supplied timezone.
        latitude: Observer latitude in degrees (north positive).
        longitude: Observer longitude in degrees (east positive).
        tz: Resolved ``pytz`` timezone the civil date is anchored to.

    Returns:
        A :class:`TwilightEvents` with the six dawn/dusk instants (each ``None``
        when the corresponding twilight does not occur on the civil day).
    """
    jd_midnight, jd_next_midnight = _civil_day_bounds(year, month, day, tz)

    # Backend flag shims (libephemeris exposes these; swisseph uses the SE_ prefix).
    calc_rise = getattr(ephe, "CALC_RISE", getattr(ephe, "SE_CALC_RISE", 1))
    calc_set = getattr(ephe, "CALC_SET", getattr(ephe, "SE_CALC_SET", 2))
    civil_bit = getattr(ephe, "BIT_CIVIL_TWILIGHT", 1024)
    nautic_bit = getattr(ephe, "BIT_NAUTIC_TWILIGHT", 2048)
    astro_bit = getattr(ephe, "BIT_ASTRO_TWILIGHT", 4096)
    geopos = (float(longitude), float(latitude), 0.0)

    # The session serializes access to the process-global backend state and
    # resets it on exit without degrading the pinned calculation mode. The base
    # flags for rise_trans stay FLG_SWIEPH, as configure_ephemeris_path yields.
    with ephemeris_session():
        iflag = configure_ephemeris_path()

        jd_noon = jd_midnight + 0.5

        def dawn(rsmi: int) -> Optional[datetime]:
            # Morning ascending crossing, within the civil day.
            jd = _next_event_jd(jd_midnight, geopos, rsmi, iflag)
            return julian_day_to_utc(jd) if jd is not None and jd < jd_next_midnight else None

        def dusk(rsmi: int) -> Optional[datetime]:
            # Evening descending crossing: searching from local noon makes the first
            # descent found the evening one (not a pre-dawn small-hours crossing). Like
            # the paired sunset it may fall in the small hours of the next civil date,
            # so the bound runs to the following local noon (rejecting far-future
            # crossings during polar day).
            jd = _next_event_jd(jd_noon, geopos, rsmi, iflag)
            return julian_day_to_utc(jd) if jd is not None and jd < jd_next_midnight + 0.5 else None

        return TwilightEvents(
            civil_dawn=dawn(calc_rise | civil_bit),
            civil_dusk=dusk(calc_set | civil_bit),
            nautical_dawn=dawn(calc_rise | nautic_bit),
            nautical_dusk=dusk(calc_set | nautic_bit),
            astronomical_dawn=dawn(calc_rise | astro_bit),
            astronomical_dusk=dusk(calc_set | astro_bit),
        )
