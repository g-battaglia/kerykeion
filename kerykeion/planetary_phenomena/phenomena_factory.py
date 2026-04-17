# -*- coding: utf-8 -*-
"""Calculate planetary phenomena (elongation, phase, magnitude, etc.).

Uses Swiss Ephemeris ``swe.pheno_ut()`` which returns:
    [0] phase angle (degrees)
    [1] phase (illuminated fraction, 0-1)
    [2] elongation (degrees from Sun)
    [3] apparent diameter (degrees)
    [4] apparent magnitude

For Mercury and Venus, the elongation and Sun position are used to
determine morning/evening star status.
"""

from __future__ import annotations

import logging
from typing import List, Optional

from kerykeion.ephemeris_backend import swe, EPHE_DATA_PATH

from kerykeion.schemas.kr_models import (
    AstrologicalSubjectModel,
    PlanetaryPhenomenaModel,
    PlanetaryPhenomenaCollectionModel,
)

logger = logging.getLogger(__name__)

_EPHE_PATH = EPHE_DATA_PATH

# Planets for which phenomena are meaningful (not fixed stars, nodes, etc.)
_PHENOMENA_PLANETS = {
    "Moon": swe.MOON,
    "Mercury": swe.MERCURY,
    "Venus": swe.VENUS,
    "Mars": swe.MARS,
    "Jupiter": swe.JUPITER,
    "Saturn": swe.SATURN,
    "Uranus": swe.URANUS,
    "Neptune": swe.NEPTUNE,
    "Pluto": swe.PLUTO,
}

# Planets that can be morning/evening stars
_INFERIOR_PLANETS = {"Mercury", "Venus"}


class PlanetaryPhenomenaFactory:
    """Calculate observational phenomena for planets."""

    @staticmethod
    def from_subject(
        subject: AstrologicalSubjectModel,
        planets: Optional[List[str]] = None,
    ) -> PlanetaryPhenomenaCollectionModel:
        """Calculate phenomena from an existing astrological subject.

        Args:
            subject: An astrological subject with a known Julian Day.
            planets: Optional list of planet names. Defaults to all planets.

        Returns:
            PlanetaryPhenomenaCollectionModel with phenomena for each planet.
        """
        return PlanetaryPhenomenaFactory._calculate(
            julian_day=subject.julian_day,
            iso_datetime=subject.iso_formatted_utc_datetime,
            planets=planets,
        )

    @staticmethod
    def from_julian_day(
        julian_day: float,
        planets: Optional[List[str]] = None,
    ) -> PlanetaryPhenomenaCollectionModel:
        """Calculate phenomena from a Julian Day number.

        Args:
            julian_day: Julian Day number.
            planets: Optional list of planet names. Defaults to all planets.

        Returns:
            PlanetaryPhenomenaCollectionModel with phenomena for each planet.
        """
        return PlanetaryPhenomenaFactory._calculate(
            julian_day=julian_day,
            iso_datetime="",
            planets=planets,
        )

    @staticmethod
    def _calculate(
        julian_day: float,
        iso_datetime: str,
        planets: Optional[List[str]] = None,
    ) -> PlanetaryPhenomenaCollectionModel:
        """Internal calculation method."""
        swe.set_ephe_path(_EPHE_PATH)
        iflag = swe.FLG_SWIEPH | swe.FLG_SPEED

        if planets is None:
            target_planets = dict(_PHENOMENA_PLANETS)
        else:
            target_planets = {k: v for k, v in _PHENOMENA_PLANETS.items() if k in planets}

        # Get Sun longitude for morning/evening star determination
        try:
            sun_data = swe.calc_ut(julian_day, swe.SUN, iflag)
            sun_lon = sun_data[0][0]
        except Exception:
            sun_lon = None

        phenomena_list: List[PlanetaryPhenomenaModel] = []

        for name, planet_id in target_planets.items():
            try:
                result = swe.pheno_ut(julian_day, planet_id, iflag)
                phase_angle = result[0]
                phase = result[1]
                elongation = result[2]
                apparent_diameter = result[3]
                apparent_magnitude = result[4]

                # Morning/evening star for Mercury and Venus
                is_morning = None
                is_evening = None
                if name in _INFERIOR_PLANETS and sun_lon is not None:
                    try:
                        planet_data = swe.calc_ut(julian_day, planet_id, iflag)
                        planet_lon = planet_data[0][0]
                        # Normalized difference
                        diff = (planet_lon - sun_lon) % 360
                        if diff > 180:
                            # Planet is west of Sun -> rises before Sun -> morning star
                            is_morning = True
                            is_evening = False
                        else:
                            is_morning = False
                            is_evening = True
                    except Exception:
                        pass

                phenomena_list.append(
                    PlanetaryPhenomenaModel(
                        name=name,
                        phase_angle=round(phase_angle, 6),
                        phase=round(phase, 6),
                        elongation=round(elongation, 6),
                        apparent_diameter=round(apparent_diameter, 8),
                        apparent_magnitude=round(apparent_magnitude, 4),
                        is_morning_star=is_morning,
                        is_evening_star=is_evening,
                    )
                )
            except Exception as e:
                logger.warning(f"Could not calculate phenomena for {name}: {e}")

        swe.close()

        return PlanetaryPhenomenaCollectionModel(
            iso_datetime=iso_datetime,
            julian_day=julian_day,
            phenomena=phenomena_list,
        )
