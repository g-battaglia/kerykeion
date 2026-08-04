# -*- coding: utf-8 -*-
"""
Low-level helpers for :class:`PlanetaryHoursFactory`.

Defines the traditional rulership tables and the pure (ephemeris-free) routine
that divides a planetary day into its twelve unequal day hours and twelve unequal
night hours, assigning each its Chaldean ruler. Keeping this logic free of any
ephemeris call makes it directly unit-testable from fixed sunrise/sunset inputs.
"""

from __future__ import annotations

from datetime import date, datetime

from kerykeion.schemas.kr_literals import ClassicalPlanet
from kerykeion.schemas.kr_models import PlanetaryHourModel

# Descending Chaldean order of orbital speed. The ruler of each successive
# planetary hour steps through this list cyclically.
CHALDEAN_ORDER: tuple[ClassicalPlanet, ...] = (
    "Saturn",
    "Jupiter",
    "Mars",
    "Sun",
    "Venus",
    "Mercury",
    "Moon",
)

# Ruler of the first hour of each weekday, indexed by Python's
# ``date.weekday()`` (Monday = 0 … Sunday = 6). This is the classical
# day-rulership that also gives each day its name (dies Lunae, dies Martis, …).
WEEKDAY_RULER: tuple[ClassicalPlanet, ...] = (
    "Moon",     # Monday
    "Mars",     # Tuesday
    "Mercury",  # Wednesday
    "Jupiter",  # Thursday
    "Venus",    # Friday
    "Saturn",   # Saturday
    "Sun",      # Sunday
)

HOURS_PER_HALF = 12


def weekday_ruler(day: date) -> ClassicalPlanet:
    """Return the planet that rules the planetary day starting on ``day``."""
    return WEEKDAY_RULER[day.weekday()]


def build_hours(
    sunrise: datetime,
    sunset: datetime,
    next_sunrise: datetime,
    day_ruler: ClassicalPlanet,
) -> list[PlanetaryHourModel]:
    """
    Build the 24 planetary hours of a planetary day.

    The twelve day hours evenly divide ``sunrise``→``sunset``; the twelve night
    hours evenly divide ``sunset``→``next_sunrise`` (so day and night hours differ
    in length unless on an equinox at the equator). The first day hour is ruled by
    ``day_ruler``; each later hour advances one step along :data:`CHALDEAN_ORDER`.

    Args:
        sunrise: Start of the day hours (timezone-aware).
        sunset: Boundary between day and night hours (timezone-aware).
        next_sunrise: End of the night hours (timezone-aware).
        day_ruler: Ruler of the first hour of the day.

    Returns:
        The 24 hours in chronological order as ``PlanetaryHourModel`` instances.

    Raises:
        ValueError: If the instants are not strictly increasing
            (``sunrise < sunset < next_sunrise``).
    """
    if not (sunrise < sunset < next_sunrise):
        raise ValueError("Planetary hours require sunrise < sunset < next_sunrise.")

    day_span = sunset - sunrise
    night_span = next_sunrise - sunset

    # Precompute the 13 boundary instants of each half so consecutive hours share
    # the exact same datetime (no microsecond drift from repeated timedelta
    # division) and the endpoints land precisely on sunrise/sunset/next_sunrise.
    day_bounds = [sunrise + day_span * (i / HOURS_PER_HALF) for i in range(HOURS_PER_HALF + 1)]
    night_bounds = [sunset + night_span * (j / HOURS_PER_HALF) for j in range(HOURS_PER_HALF + 1)]
    day_bounds[0], day_bounds[HOURS_PER_HALF] = sunrise, sunset
    night_bounds[0], night_bounds[HOURS_PER_HALF] = sunset, next_sunrise

    start_index = CHALDEAN_ORDER.index(day_ruler)

    hours: list[PlanetaryHourModel] = []
    for i in range(2 * HOURS_PER_HALF):
        ruler = CHALDEAN_ORDER[(start_index + i) % len(CHALDEAN_ORDER)]
        if i < HOURS_PER_HALF:
            start, end, is_diurnal = day_bounds[i], day_bounds[i + 1], True
        else:
            night_step = i - HOURS_PER_HALF
            start, end, is_diurnal = night_bounds[night_step], night_bounds[night_step + 1], False
        hours.append(
            PlanetaryHourModel(
                index=i + 1,
                ruler=ruler,
                is_diurnal=is_diurnal,
                start=start,
                end=end,
            )
        )
    return hours
