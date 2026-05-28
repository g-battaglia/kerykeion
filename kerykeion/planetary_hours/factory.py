# -*- coding: utf-8 -*-
"""
This is part of Kerykeion (C) 2025 Giacomo Battaglia
"""

from __future__ import annotations

from datetime import date, timedelta, timezone

from kerykeion.planetary_hours.utils import build_hours, weekday_ruler
from kerykeion.schemas.kerykeion_exception import KerykeionException
from kerykeion.schemas.kr_models import PlanetaryHoursModel
from kerykeion.sun_times.utils import compute_sun_events, localize_datetime, resolve_timezone

_POLAR_MESSAGE = (
    "Planetary hours are undefined when the Sun does not rise and set (polar day/night) at this location and date."
)


class PlanetaryHoursFactory:
    """
    Factory for the planetary (Chaldean) hours of a moment at a location.

    A *planetary day* runs from one sunrise to the next. Its daytime is split into
    twelve equal day hours and its night into twelve equal night hours; because
    daylight and night rarely last the same, day and night hours differ in length
    (the "unequal" or "temporal" hours of antiquity). The first hour of the day is
    ruled by the planet of the weekday (Monday→Moon, Tuesday→Mars, …); each later
    hour advances one step along the descending Chaldean order (Saturn, Jupiter,
    Mars, Sun, Venus, Mercury, Moon), cycling through all 24.

    A moment falling before the day's sunrise belongs to the *previous* planetary
    day (it is still in that day's night hours), which this factory resolves
    automatically.

    Example:
        >>> from kerykeion import PlanetaryHoursFactory
        >>> ph = PlanetaryHoursFactory.from_datetime(
        ...     2026, 5, 28, 11, 30, latitude=41.9028, longitude=12.4964,
        ...     tz_str="Europe/Rome")
        >>> ph.day_ruler, ph.current_ruler, len(ph.hours)
        ('Jupiter', ..., 24)

    Note:
        Sunrise/sunset come from the apparent (refracted) upper limb, matching the
        :class:`~kerykeion.sun_times.factory.SunTimesFactory` convention. Planetary
        hours are undefined under polar day/night, which raises
        ``KerykeionException``.
    """

    @classmethod
    def from_datetime(
        cls,
        year: int,
        month: int,
        day: int,
        hour: int,
        minute: int = 0,
        *,
        latitude: float,
        longitude: float,
        tz_str: str,
    ) -> PlanetaryHoursModel:
        """
        Compute the planetary hours for the planetary day containing a moment.

        Args:
            year: Gregorian civil year (1-9999 CE).
            month: Civil month (1-12).
            day: Civil day (1-31).
            hour: Hour of day (0-23) in ``tz_str``.
            minute: Minute (0-59) in ``tz_str``. Defaults to 0.
            latitude: Observer latitude in degrees, north positive (-90 to 90).
            longitude: Observer longitude in degrees, east positive (-180 to 180).
            tz_str: IANA timezone identifier the clock time is expressed in.

        Returns:
            PlanetaryHoursModel: the day ruler, the current hour (index + ruler),
            the bounding sunrise/sunset/next-sunrise, and the full 24-hour table.

        Raises:
            KerykeionException: If ``tz_str`` is invalid, or if the Sun does not
                rise and set on the relevant date (polar day/night).
        """
        tz = resolve_timezone(tz_str)
        moment_utc = localize_datetime(year, month, day, hour, minute, tz=tz).astimezone(timezone.utc)

        today = compute_sun_events(year, month, day, latitude, longitude, tz)
        if today.sunrise is None:
            raise KerykeionException(_POLAR_MESSAGE)

        if moment_utc >= today.sunrise:
            # The moment is within today's planetary day (sunrise → next sunrise).
            if today.sunset is None:
                raise KerykeionException(_POLAR_MESSAGE)
            tomorrow = date(year, month, day) + timedelta(days=1)
            next_events = compute_sun_events(tomorrow.year, tomorrow.month, tomorrow.day, latitude, longitude, tz)
            if next_events.sunrise is None:
                raise KerykeionException(_POLAR_MESSAGE)
            sunrise, sunset, next_sunrise = today.sunrise, today.sunset, next_events.sunrise
        else:
            # Before today's sunrise → still in the previous planetary day's night.
            yesterday = date(year, month, day) - timedelta(days=1)
            prev_events = compute_sun_events(yesterday.year, yesterday.month, yesterday.day, latitude, longitude, tz)
            if prev_events.sunrise is None or prev_events.sunset is None:
                raise KerykeionException(_POLAR_MESSAGE)
            sunrise, sunset, next_sunrise = prev_events.sunrise, prev_events.sunset, today.sunrise

        # The planetary day is named by the civil (local) date of its sunrise.
        day_date = sunrise.astimezone(tz).date()
        day_ruler = weekday_ruler(day_date)
        hours = build_hours(sunrise, sunset, next_sunrise, day_ruler)

        current = next((h for h in hours if h.start <= moment_utc < h.end), hours[-1])

        return PlanetaryHoursModel(
            date=day_date.isoformat(),
            timezone=tz_str,
            latitude=latitude,
            longitude=longitude,
            day_ruler=day_ruler,
            current_index=current.index,
            current_ruler=current.ruler,
            sunrise=sunrise,
            sunset=sunset,
            next_sunrise=next_sunrise,
            hours=hours,
        )
