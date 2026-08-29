# -*- coding: utf-8 -*-
"""Calculate planetary phenomena (elongation, phase, magnitude, etc.).

Uses Swiss Ephemeris ``ephe.pheno_ut()`` which returns:
    [0] phase angle (degrees)
    [1] phase (illuminated fraction, 0-1)
    [2] elongation (degrees from Sun)
    [3] apparent diameter (degrees)
    [4] apparent magnitude

For Mercury and Venus, the elongation and Sun position are used to
determine morning/evening star status. That pair of flags is purely
geometric — which side of the Sun the planet stands on — and says nothing
about whether the planet can actually be seen. Visibility is a separate
field, ``solar_phase``: it reads the elongation against three configurable
cut-offs and names the body cazimi, combust, under the beams, or free.
"""

from __future__ import annotations

import logging
from typing import List, Optional

from kerykeion.ephemeris_backend.backend import ephe, ephemeris_session
from kerykeion.predictive.utils import validate_julian_day
from kerykeion.schemas.exceptions import KerykeionException
from kerykeion.settings.config_constants import POINT_NUMBER_MAP

from kerykeion.schemas.literals import SolarPhase
from kerykeion.schemas.models import (
    AstrologicalSubjectModel,
    PlanetaryPhenomenaModel,
    PlanetaryPhenomenaCollectionModel,
    SolarPhaseThresholdsModel,
)

logger = logging.getLogger(__name__)

# Planets for which phenomena are meaningful (not fixed stars, nodes, etc.)
_PHENOMENA_PLANETS = {
    name: POINT_NUMBER_MAP[name]
    for name in ("Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto")
}

# Planets that can be morning/evening stars
_INFERIOR_PLANETS = {"Mercury", "Venus"}


def classify_solar_phase(elongation: float, thresholds: SolarPhaseThresholdsModel) -> SolarPhase:
    """Name a body's condition relative to the Sun from its elongation.

    The cut-offs are walked from the inside out and every comparison is strict,
    so a body sitting exactly on one takes the outer name.

    The argument is the elongation as the ephemeris reports it: a TRUE angular
    separation, latitude included. It is not the difference in ecliptic
    longitude, which is what the tradition's tables were built on. The two part
    company for a body off the ecliptic — Mercury can share the Sun's longitude
    while standing three degrees away from it in the sky — and the separation is
    the honest quantity to ask about visibility, so it is the one used here.

    Args:
        elongation: Angular distance from the Sun in degrees (0-180).
        thresholds: The three cut-offs to read it against.

    Returns:
        One of ``"cazimi"``, ``"combust"``, ``"under_the_beams"``, ``"free"``.
    """
    if elongation < thresholds.cazimi_deg:
        return "cazimi"
    if elongation < thresholds.combust_deg:
        return "combust"
    if elongation < thresholds.under_beams_deg:
        return "under_the_beams"
    return "free"


class PlanetaryPhenomenaFactory:
    """Calculate observational phenomena for planets.

    Computes elongation, illumination fraction, phase angle, apparent
    diameter/magnitude, morning/evening star status, and the condition
    relative to the Sun (``solar_phase``).

    Example:
        >>> from kerykeion import PlanetaryPhenomenaFactory
        >>> results = PlanetaryPhenomenaFactory.from_subject(subject)
    """

    @staticmethod
    def from_subject(
        subject: AstrologicalSubjectModel,
        planets: Optional[List[str]] = None,
        solar_phase_thresholds: Optional[SolarPhaseThresholdsModel] = None,
    ) -> PlanetaryPhenomenaCollectionModel:
        """Calculate phenomena from an existing astrological subject.

        Args:
            subject: An astrological subject with a known Julian Day.
            planets: Optional list of planet names. Defaults to all planets.
            solar_phase_thresholds: Optional cut-offs for ``solar_phase``.
                Defaults to the classical 0.2833° / 8.5° / 17°; whatever is
                used is echoed on the returned collection.

        Returns:
            PlanetaryPhenomenaCollectionModel with phenomena for each planet.
        """
        # julian_day is Optional on the model (composite subjects have no
        # single moment in time); without this guard every pheno_ut call fails
        # on the None and the all-failed check below raises a misleading
        # "backend may be unavailable" error. Mirrors PrimaryDirectionsFactory's
        # _require_geometry guard.
        if subject.julian_day is None:
            raise KerykeionException(
                "Subject is missing Julian Day — cannot compute planetary phenomena "
                "(composite subjects are not supported here)."
            )
        return PlanetaryPhenomenaFactory._calculate(
            julian_day=subject.julian_day,
            iso_datetime=subject.iso_formatted_utc_datetime,
            planets=planets,
            solar_phase_thresholds=solar_phase_thresholds,
        )

    @staticmethod
    def from_julian_day(
        julian_day: float,
        planets: Optional[List[str]] = None,
        solar_phase_thresholds: Optional[SolarPhaseThresholdsModel] = None,
    ) -> PlanetaryPhenomenaCollectionModel:
        """Calculate phenomena from a Julian Day number.

        Args:
            julian_day: Julian Day number.
            planets: Optional list of planet names. Defaults to all planets.
            solar_phase_thresholds: Optional cut-offs for ``solar_phase``.
                Defaults to the classical 0.2833° / 8.5° / 17°; whatever is
                used is echoed on the returned collection.

        Returns:
            PlanetaryPhenomenaCollectionModel with phenomena for each planet.
        """
        return PlanetaryPhenomenaFactory._calculate(
            julian_day=julian_day,
            iso_datetime="",
            planets=planets,
            solar_phase_thresholds=solar_phase_thresholds,
        )

    @staticmethod
    def _calculate(
        julian_day: float,
        iso_datetime: str,
        planets: Optional[List[str]] = None,
        solar_phase_thresholds: Optional[SolarPhaseThresholdsModel] = None,
    ) -> PlanetaryPhenomenaCollectionModel:
        """Compute elongation, illumination, and visibility for each planet."""
        validate_julian_day(julian_day)
        thresholds = solar_phase_thresholds or SolarPhaseThresholdsModel()
        if planets is None:
            target_planets = dict(_PHENOMENA_PLANETS)
        else:
            # Reject unknown/mistyped/wrong-case names rather than silently
            # dropping them into an empty result (e.g. ['mercury'] or ['Venuss']
            # would return no phenomena with no signal). Consistent with the
            # ingress/station/nodes factories.
            invalid = sorted(set(planets) - set(_PHENOMENA_PLANETS))
            if invalid:
                raise ValueError(
                    f"Unknown planets: {', '.join(invalid)}. "
                    f"Valid: {', '.join(_PHENOMENA_PLANETS)}"
                )
            target_planets = {k: v for k, v in _PHENOMENA_PLANETS.items() if k in planets}

        phenomena_list: List[PlanetaryPhenomenaModel] = []

        with ephemeris_session() as iflag:
            # Get Sun longitude for morning/evening star determination
            try:
                sun_data = ephe.calc_ut(julian_day, ephe.SUN, iflag)
                sun_lon = sun_data[0][0]
            except Exception:
                sun_lon = None

            for name, planet_id in target_planets.items():
                try:
                    result = ephe.pheno_ut(julian_day, planet_id, iflag)
                    phase_angle = result[0]
                    phase = result[1]
                    elongation = result[2]
                    apparent_diameter = result[3]
                    apparent_magnitude = result[4]

                    # The published elongation is the rounded one, so the label
                    # is read off the same number a consumer sees: a value that
                    # rounds onto a cut-off must not be named one thing in the
                    # field and another in the phase.
                    rounded_elongation = round(elongation, 6)

                    # Named for EVERY body in the set, the Moon included. Its
                    # elongation is the same astronomical quantity (angular
                    # distance from the Sun) and the names still describe what
                    # they always describe — the dark of the Moon is exactly the
                    # interval in which it is under the beams, and a central
                    # solar eclipse is the one moment it is cazimi. What a given
                    # school then DOES with a combust Moon is the school's
                    # business, not this factory's; withholding the datum would
                    # be a judgement, and the library does not make those.
                    solar_phase = classify_solar_phase(rounded_elongation, thresholds)

                    # Morning/evening star for Mercury and Venus. Geometry only:
                    # the sign of the longitude difference, with no visibility
                    # threshold of any kind. A planet one degree from the Sun is
                    # still "an evening star" here — invisible, but east of it.
                    # This is deliberate and unchanged; solar_phase above is
                    # where visibility is expressed.
                    is_morning = None
                    is_evening = None
                    if name in _INFERIOR_PLANETS and sun_lon is not None:
                        try:
                            planet_data = ephe.calc_ut(julian_day, planet_id, iflag)
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
                            elongation=rounded_elongation,
                            apparent_diameter=round(apparent_diameter, 8),
                            apparent_magnitude=round(apparent_magnitude, 4),
                            is_morning_star=is_morning,
                            is_evening_star=is_evening,
                            solar_phase=solar_phase,
                        )
                    )
                except Exception as e:
                    logger.warning(f"Could not calculate phenomena for {name}: {e}")

        # Tolerate individual-planet failures, but surface the all-failed case
        # (an empty result is otherwise indistinguishable from a valid "no
        # phenomena"). Parity with PlanetaryNodesFactory.
        if target_planets and not phenomena_list:
            raise KerykeionException(
                "Failed to calculate phenomena for all requested planets "
                f"({', '.join(target_planets)}); the ephemeris backend may be "
                "unavailable or out of range. See logs for per-planet errors."
            )

        return PlanetaryPhenomenaCollectionModel(
            iso_datetime=iso_datetime,
            julian_day=julian_day,
            phenomena=phenomena_list,
            solar_phase_thresholds=thresholds,
        )
