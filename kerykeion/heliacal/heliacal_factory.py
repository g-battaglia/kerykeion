# -*- coding: utf-8 -*-
"""
Heliacal Risings and Settings Factory
======================================

Calculates heliacal events (first/last visibility of planets and stars
relative to the Sun) using the Swiss Ephemeris ``swe.heliacal_ut()``
function.

A heliacal rising is the first morning a celestial body becomes visible
above the eastern horizon just before sunrise after a period of
invisibility.  A heliacal setting is the last evening it is visible
above the western horizon just after sunset.

This is part of Kerykeion (C) 2025 Giacomo Battaglia
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

import swisseph as swe

from kerykeion.schemas.kr_models import SubscriptableBaseModel

logger = logging.getLogger(__name__)

# ---- Event-type constants (mirrors Swiss Ephemeris) ----
HELIACAL_RISING: int = swe.HELIACAL_RISING    # 1 - morning first
HELIACAL_SETTING: int = swe.HELIACAL_SETTING  # 2 - evening last
EVENING_FIRST: int = swe.EVENING_FIRST        # 3
MORNING_LAST: int = swe.MORNING_LAST          # 4

EVENT_TYPE_LABELS = {
    HELIACAL_RISING: "heliacal_rising",
    HELIACAL_SETTING: "heliacal_setting",
    EVENING_FIRST: "evening_first",
    MORNING_LAST: "morning_last",
}

# ---- Default atmospheric / observer parameters ----
DEFAULT_PRESSURE: float = 1013.25   # mbar (hPa)
DEFAULT_TEMPERATURE: float = 15.0   # Celsius
DEFAULT_HUMIDITY: float = 40.0      # percent
DEFAULT_EXTINCTION: float = 0.2     # extinction coefficient

DEFAULT_ATMO: Tuple[float, float, float, float] = (
    DEFAULT_PRESSURE,
    DEFAULT_TEMPERATURE,
    DEFAULT_HUMIDITY,
    DEFAULT_EXTINCTION,
)

DEFAULT_OBSERVER: Tuple[float, float, float, float, float, float] = (
    36.0,  # age of observer in years
    1.0,   # Snellen ratio (1 = normal vision)
    0.0,   # monocular (0) / binocular (1)
    0.0,   # telescope magnification (0 = naked eye default)
    0.0,   # optical aperture in mm
    0.0,   # optical transmission
)

# Planets supported by swe.heliacal_ut
PLANETS = ("Mercury", "Venus", "Mars", "Jupiter", "Saturn")

# Inner planets support all four event types; outer planets only rising/setting.
INNER_PLANETS = {"Mercury", "Venus"}


# ---- Data model ----
class HeliacalEventModel(SubscriptableBaseModel):
    """Model representing a single heliacal event."""

    event_type: str
    """Human-readable event type, e.g. 'heliacal_rising'."""

    julian_day: float
    """Julian Day (UT) of the start of visibility."""

    planet_name: str
    """Name of the planet or star."""

    datestamp: str
    """ISO-style date string (YYYY-MM-DD) for quick reference."""


# ---- Factory ----
class HeliacalFactory:
    """Find heliacal rising and setting events for planets.

    Usage::

        factory = HeliacalFactory()
        event = factory.next_heliacal_rising(
            julian_day=2461125.5,
            planet_name_or_star="Venus",
            geopos=(12.4964, 41.9028, 50),
        )
        print(event.datestamp)

    Parameters
    ----------
    ephe_path : str or None
        Path to the Swiss Ephemeris data directory.  Defaults to the
        ``kerykeion/sweph`` directory shipped with the library.
    """

    def __init__(self, ephe_path: Optional[str] = None) -> None:
        if ephe_path is None:
            ephe_path = str(Path(__file__).parents[1].absolute() / "sweph")
        swe.set_ephe_path(ephe_path)

    # ------------------------------------------------------------------ #
    #  Public API                                                         #
    # ------------------------------------------------------------------ #

    def next_heliacal_rising(
        self,
        julian_day: float,
        planet_name_or_star: str,
        geopos: Tuple[float, float, float],
        atmo: Optional[Tuple[float, float, float, float]] = None,
        observer: Optional[Tuple[float, float, float, float, float, float]] = None,
    ) -> HeliacalEventModel:
        """Find the next heliacal rising after *julian_day*.

        Parameters
        ----------
        julian_day:
            Starting Julian Day (UT).
        planet_name_or_star:
            Planet name (e.g. ``"Venus"``) or fixed-star name.
        geopos:
            ``(longitude, latitude, altitude_m)`` of the observer.
        atmo:
            ``(pressure, temperature, humidity, extinction)``; uses
            sensible defaults when *None*.
        observer:
            Observer parameters tuple of length 6; uses defaults when
            *None*.

        Returns
        -------
        HeliacalEventModel
        """
        result = self._find_event(
            julian_day=julian_day,
            planet_name_or_star=planet_name_or_star,
            geopos=geopos,
            event_type=HELIACAL_RISING,
            atmo=atmo,
            observer=observer,
        )
        swe.close()
        return result

    def search_events(
        self,
        julian_day: float,
        geopos: Tuple[float, float, float],
        count: int = 5,
        planets: Optional[Sequence[str]] = None,
        event_types: Optional[Sequence[int]] = None,
        atmo: Optional[Tuple[float, float, float, float]] = None,
        observer: Optional[Tuple[float, float, float, float, float, float]] = None,
    ) -> List[HeliacalEventModel]:
        """Find the next *count* heliacal events across multiple planets.

        Events are returned sorted by Julian Day (chronologically).

        Parameters
        ----------
        julian_day:
            Starting Julian Day (UT).
        geopos:
            ``(longitude, latitude, altitude_m)`` of the observer.
        count:
            Maximum number of events to return.
        planets:
            Planet names to scan.  Defaults to all five visible planets.
        event_types:
            Event type constants to look for.  Defaults to
            ``[HELIACAL_RISING, HELIACAL_SETTING]``.
        atmo:
            Atmospheric parameters; uses defaults when *None*.
        observer:
            Observer parameters; uses defaults when *None*.

        Returns
        -------
        list[HeliacalEventModel]
        """
        if planets is None:
            planets = PLANETS
        if event_types is None:
            event_types = [HELIACAL_RISING, HELIACAL_SETTING]

        events: List[HeliacalEventModel] = []

        for planet in planets:
            for etype in event_types:
                # Skip event types that only apply to inner planets
                if etype in (EVENING_FIRST, MORNING_LAST) and planet not in INNER_PLANETS:
                    continue
                try:
                    event = self._find_event(
                        julian_day=julian_day,
                        planet_name_or_star=planet,
                        geopos=geopos,
                        event_type=etype,
                        atmo=atmo,
                        observer=observer,
                    )
                    events.append(event)
                except Exception as exc:
                    logger.debug(
                        "Skipping %s %s: %s",
                        planet,
                        EVENT_TYPE_LABELS.get(etype, etype),
                        exc,
                    )

        # Sort chronologically and trim to *count*.
        events.sort(key=lambda e: e.julian_day)
        swe.close()
        return events[:count]

    # ------------------------------------------------------------------ #
    #  Internal helpers                                                    #
    # ------------------------------------------------------------------ #

    def _find_event(
        self,
        julian_day: float,
        planet_name_or_star: str,
        geopos: Tuple[float, float, float],
        event_type: int,
        atmo: Optional[Tuple[float, float, float, float]],
        observer: Optional[Tuple[float, float, float, float, float, float]],
    ) -> HeliacalEventModel:
        """Low-level wrapper around ``swe.heliacal_ut``."""
        if atmo is None:
            atmo = DEFAULT_ATMO
        if observer is None:
            observer = DEFAULT_OBSERVER

        dret = swe.heliacal_ut(
            julian_day,
            geopos,
            atmo,
            observer,
            planet_name_or_star,
            event_type,
            0,  # flags
        )

        result_jd = dret[0]  # start of visibility

        # Convert Julian Day to a calendar date for the datestamp.
        year, month, day, _hour = swe.revjul(result_jd)
        datestamp = f"{int(year):04d}-{int(month):02d}-{int(day):02d}"

        return HeliacalEventModel(
            event_type=EVENT_TYPE_LABELS.get(event_type, str(event_type)),
            julian_day=result_jd,
            planet_name=planet_name_or_star,
            datestamp=datestamp,
        )
