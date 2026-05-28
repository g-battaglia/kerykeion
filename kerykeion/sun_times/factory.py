# -*- coding: utf-8 -*-
"""
This is part of Kerykeion (C) 2025 Giacomo Battaglia
"""

from __future__ import annotations

from kerykeion.schemas.kr_models import SunTimesModel
from kerykeion.sun_times.utils import compute_sun_events, resolve_timezone


class SunTimesFactory:
    """
    Factory for sunrise / sunset / solar-noon / day-length at a place and date.

    This is a lightweight, location-only calculation: it queries the active
    ephemeris backend's rise/set routine directly (with atmospheric refraction)
    rather than building a full astrological subject, so it is fast and has no
    geolocation dependency. Times are returned as timezone-aware UTC datetimes;
    on polar day/night or transition dates the derived ``solar_noon`` and
    ``day_length`` are ``None`` unless a sunrise can be paired with a later sunset.

    Example:
        >>> from kerykeion import SunTimesFactory
        >>> sun = SunTimesFactory.from_date(2026, 5, 28, latitude=41.9028,
        ...                                 longitude=12.4964, tz_str="Europe/Rome")
        >>> sun.sunrise.isoformat()
        '2026-05-28T03:39:...+00:00'
        >>> str(sun.day_length)
        '15:0...'

    Note:
        The result is the apparent (refracted) upper-limb sunrise/sunset, the
        convention used by civil timekeeping.
    """

    @classmethod
    def from_date(
        cls,
        year: int,
        month: int,
        day: int,
        *,
        latitude: float,
        longitude: float,
        tz_str: str,
    ) -> SunTimesModel:
        """
        Compute sun times for a civil date at a location.

        Args:
            year: Gregorian civil year (1-9999 CE).
            month: Civil month (1-12).
            day: Civil day (1-31).
            latitude: Observer latitude in degrees, north positive (-90 to 90).
            longitude: Observer longitude in degrees, east positive (-180 to 180).
            tz_str: IANA timezone identifier the civil date is anchored to.

        Returns:
            SunTimesModel: sunrise, sunset, solar noon, day length and polar flags.

        Raises:
            KerykeionException: If ``tz_str`` is invalid or the civil date is unsupported.
        """
        tz = resolve_timezone(tz_str)
        events = compute_sun_events(year, month, day, latitude, longitude, tz)

        return SunTimesModel(
            date=f"{year:04d}-{month:02d}-{day:02d}",
            timezone=tz_str,
            latitude=latitude,
            longitude=longitude,
            sunrise=events.sunrise,
            sunset=events.sunset,
            solar_noon=events.solar_noon,
            day_length=events.day_length,
            is_polar_day=events.is_polar_day,
            is_polar_night=events.is_polar_night,
        )
