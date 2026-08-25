# -*- coding: utf-8 -*-
"""
This is part of Kerykeion (C) 2025 Giacomo Battaglia
"""

from __future__ import annotations

from datetime import date, timedelta, timezone

from kerykeion.planetary_hours.utils import build_hours, weekday_ruler
from kerykeion.schemas.exceptions import KerykeionException
from kerykeion.schemas.models import PlanetaryHoursModel
from kerykeion.sun_times.utils import compute_sun_events, localize_datetime, resolve_timezone

_POLAR_MESSAGE = (
    "Planetary hours are undefined when the Sun does not rise and set (polar day/night) at this location and date."
)


def _civil_day_beside(year: int, month: int, day: int, offset_days: int) -> date:
    """The civil date ``offset_days`` away, or a clean refusal at either end of the range.

    A planetary day runs from one sunrise to the next, so the last evening of
    9999 needs a sunrise on 10000-01-01 and the first morning of year 1 needs a
    sunset on the day before it; ``date`` has neither and raises ``OverflowError``.
    Only the full-range ephemeris ever gets this far — on a narrower kernel the
    coverage check refuses first — which is how the raw error went unseen.
    """
    try:
        return date(year, month, day) + timedelta(days=offset_days)
    except OverflowError as exc:
        which = "after" if offset_days > 0 else "before"
        raise KerykeionException(
            f"Planetary hours for {year:04d}-{month:02d}-{day:02d} need the sunrise of the day {which} it, "
            f"and there is no civil date {which} this one: the library represents years 1 to 9999."
        ) from exc


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
            KerykeionException: If ``tz_str`` is invalid, the latitude/longitude
                is out of range, or if the Sun does not rise and set on the
                relevant date (polar day/night).
        """
        if not -90.0 <= latitude <= 90.0:
            raise KerykeionException(
                f"Latitude {latitude} is out of range; it must be between -90 and 90 degrees."
            )
        if not -180.0 <= longitude <= 180.0:
            raise KerykeionException(
                f"Longitude {longitude} is out of range; it must be between -180 and 180 degrees."
            )
        tz = resolve_timezone(tz_str)
        moment_utc = localize_datetime(year, month, day, hour, minute, tz=tz).astimezone(timezone.utc)

        today = compute_sun_events(year, month, day, latitude, longitude, tz)
        if today.sunrise is None:
            raise KerykeionException(_POLAR_MESSAGE)

        if moment_utc >= today.sunrise:
            # The moment is within today's planetary day (sunrise → next sunrise).
            if today.sunset is None:
                raise KerykeionException(_POLAR_MESSAGE)
            tomorrow = _civil_day_beside(year, month, day, +1)
            next_events = compute_sun_events(tomorrow.year, tomorrow.month, tomorrow.day, latitude, longitude, tz)
            if next_events.sunrise is None:
                raise KerykeionException(_POLAR_MESSAGE)
            sunrise, sunset, next_sunrise = today.sunrise, today.sunset, next_events.sunrise
        else:
            # Before today's sunrise → still in the previous planetary day's night.
            yesterday = _civil_day_beside(year, month, day, -1)
            prev_events = compute_sun_events(yesterday.year, yesterday.month, yesterday.day, latitude, longitude, tz)
            if prev_events.sunrise is None or prev_events.sunset is None:
                raise KerykeionException(_POLAR_MESSAGE)
            sunrise, sunset, next_sunrise = prev_events.sunrise, prev_events.sunset, today.sunrise

        # The planetary day is named by the civil (local) date of its sunrise.
        day_date = sunrise.astimezone(tz).date()
        day_ruler = weekday_ruler(day_date)
        # On degenerate high-latitude transition days the bounding instants may
        # not be strictly increasing; surface that as a KerykeionException rather
        # than letting build_hours' raw ValueError escape.
        try:
            hours = build_hours(sunrise, sunset, next_sunrise, day_ruler)
        except ValueError as exc:
            raise KerykeionException(_POLAR_MESSAGE) from exc

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
