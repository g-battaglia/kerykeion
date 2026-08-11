# -*- coding: utf-8 -*-
"""Calculate planetary nodes and apsides for any planet.

For each planet, computes:
- Ascending node: where the orbit crosses the ecliptic northward
- Descending node: where the orbit crosses southward
- Perihelion: closest point to the Sun
- Aphelion: farthest point from the Sun

The Sun is NOT supported: it has no geocentric orbital nodes or apsides
(the ephemeris returns all-zero placeholders for it), so it is excluded
from the defaults and an explicit request for it raises a
:class:`KerykeionException`.

Swiss Ephemeris function: ephe.nod_aps_ut(jd_ut, planet, method, iflag)
Methods: NODBIT_MEAN (mean elements), NODBIT_OSCU (osculating/instantaneous)
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

from kerykeion.ephemeris_backend import ephe, ephemeris_session
from kerykeion.predictive.utils import validate_julian_day

from kerykeion.schemas import KerykeionException
from kerykeion.schemas.literals import AstrologicalPoint
from kerykeion.schemas.models import (
    AstrologicalSubjectModel,
    KerykeionPointModel,
    SubscriptableBaseModel,
)
from kerykeion.utilities import get_kerykeion_point_from_degree
from pydantic import Field

logger = logging.getLogger(__name__)

NODBIT_MEAN = getattr(ephe, "NODBIT_MEAN", 1)
NODBIT_OSCU = getattr(ephe, "NODBIT_OSCU", 2)

# The Sun is deliberately absent: nod_aps_ut has no geocentric solar
# nodes/apsides to return and yields all-zero placeholders for it.
_NODE_PLANETS: Dict[AstrologicalPoint, int] = {
    "Moon": ephe.MOON,
    "Mercury": ephe.MERCURY,
    "Venus": ephe.VENUS,
    "Mars": ephe.MARS,
    "Jupiter": ephe.JUPITER,
    "Saturn": ephe.SATURN,
    "Uranus": ephe.URANUS,
    "Neptune": ephe.NEPTUNE,
    "Pluto": ephe.PLUTO,
}


class PlanetaryNodeModel(SubscriptableBaseModel):
    """Nodes and apsides for a single planet."""
    planet_name: str
    ascending_node: KerykeionPointModel
    descending_node: KerykeionPointModel
    perihelion: KerykeionPointModel
    aphelion: KerykeionPointModel


class PlanetaryNodesCollectionModel(SubscriptableBaseModel):
    """Collection of planetary nodes for a specific moment."""
    iso_datetime: str = Field(default="")
    julian_day: float
    method: str = Field(description="Calculation method: 'mean' or 'osculating'")
    nodes: List[PlanetaryNodeModel]


class PlanetaryNodesFactory:
    """Calculate planetary nodes and apsides for any planet (except the Sun).

    Computes ascending/descending nodes and perihelion/aphelion
    in both mean and osculating modes.

    Example:
        >>> from kerykeion import PlanetaryNodesFactory
        >>> results = PlanetaryNodesFactory.from_subject(subject, method="mean")
    """

    @staticmethod
    def from_subject(
        subject: AstrologicalSubjectModel,
        method: str = "mean",
        planets: Optional[List[str]] = None,
    ) -> PlanetaryNodesCollectionModel:
        """Calculate nodes from an existing astrological subject.

        The node/apsis longitudes (and the sign metadata derived from them)
        are computed in the subject's own zodiac frame: a sidereal subject
        gets sidereal node longitudes, consistent with the rest of its chart.

        Args:
            subject: An astrological subject.
            method: "mean" or "osculating".
            planets: Optional list of planet names. Defaults to all
                supported planets (Moon through Pluto). Requesting "Sun"
                raises a :class:`KerykeionException` — the Sun has no
                geocentric nodes or apsides.
        """
        # julian_day is Optional on the model (composite subjects have no
        # single moment in time); without this guard it reaches
        # get_ayanamsa_ex_ut / nod_aps_ut as None and raises a raw,
        # undiagnosable TypeError. Mirrors PrimaryDirectionsFactory's
        # _require_geometry guard.
        if subject.julian_day is None:
            raise KerykeionException(
                "Subject is missing Julian Day — cannot compute planetary nodes "
                "(composite subjects are not supported here)."
            )
        return PlanetaryNodesFactory._calculate(
            julian_day=subject.julian_day,
            iso_datetime=subject.iso_formatted_utc_datetime,
            method=method,
            planets=planets,
            zodiac_type=getattr(subject, "zodiac_type", None),
            sidereal_mode=getattr(subject, "sidereal_mode", None),
            custom_ayanamsa_t0=getattr(subject, "custom_ayanamsa_t0", None),
            custom_ayanamsa_ayan_t0=getattr(subject, "custom_ayanamsa_ayan_t0", None),
        )

    @staticmethod
    def from_julian_day(
        julian_day: float,
        method: str = "mean",
        planets: Optional[List[str]] = None,
    ) -> PlanetaryNodesCollectionModel:
        """Calculate nodes from a Julian Day number (tropical zodiac)."""
        return PlanetaryNodesFactory._calculate(
            julian_day=julian_day,
            iso_datetime="",
            method=method,
            planets=planets,
        )

    @staticmethod
    def _calculate(
        julian_day: float,
        iso_datetime: str,
        method: str,
        planets: Optional[List[str]],
        zodiac_type: Optional[str] = None,
        sidereal_mode: Optional[str] = None,
        custom_ayanamsa_t0: Optional[float] = None,
        custom_ayanamsa_ayan_t0: Optional[float] = None,
    ) -> PlanetaryNodesCollectionModel:
        """Compute nodes/apsides for all requested planets at a given Julian Day.

        The ephemeris session is configured with the requested zodiac. The
        node/apsis longitudes themselves are always computed tropically
        (``FLG_SIDEREAL`` is masked out of the ``nod_aps_ut`` call — not every
        backend applies it there) and rotated into the sidereal frame by
        subtracting the session's ayanamsa, which is deterministic on both
        backends.
        """
        validate_julian_day(julian_day)
        if method not in ("mean", "osculating"):
            # Without this, any other string (e.g. "Mean") silently selected
            # the osculating branch while the model echoed the caller's label.
            raise KerykeionException(
                f"Invalid nodes method {method!r}: expected 'mean' or 'osculating'."
            )
        nodbit = NODBIT_MEAN if method == "mean" else NODBIT_OSCU

        if planets is not None and "Sun" in planets:
            raise KerykeionException(
                "The Sun has no geocentric orbital nodes or apsides (the ephemeris "
                "returns all-zero placeholders for it). Remove 'Sun' from the "
                "requested planets."
            )

        # Reject unknown/mistyped names rather than silently dropping them —
        # planets=['Jupiter','Pluot'] would otherwise compute only Jupiter, and
        # planets=['Pluot'] would return an empty result with no error (the
        # all-failed guard below never fires on an empty target set). Consistent
        # with SignIngressFactory / RetrogradeStationFactory.
        if planets is not None:
            invalid = sorted(set(planets) - set(_NODE_PLANETS) - {"Sun"})
            if invalid:
                raise ValueError(
                    f"Unknown planets: {', '.join(invalid)}. "
                    f"Valid: {', '.join(_NODE_PLANETS)}"
                )

        target_planets = _NODE_PLANETS if planets is None else {
            k: v for k, v in _NODE_PLANETS.items() if k in planets
        }

        node_results: List[PlanetaryNodeModel] = []

        with ephemeris_session(
            zodiac_type=zodiac_type,
            sidereal_mode=sidereal_mode,
            custom_ayanamsa_t0=custom_ayanamsa_t0,
            custom_ayanamsa_ayan_t0=custom_ayanamsa_ayan_t0,
        ) as iflag:
            ayanamsa = 0.0
            if iflag & ephe.FLG_SIDEREAL:
                ayanamsa = float(ephe.get_ayanamsa_ex_ut(julian_day, iflag)[1])
            calc_iflag = iflag & ~ephe.FLG_SIDEREAL

            for name, planet_id in target_planets.items():
                try:
                    # Signature on both backends is (jd_ut, planet, method, flags):
                    # passing flags third would be read as `method`, silently
                    # turning every "mean" request into osculating values.
                    result = ephe.nod_aps_ut(julian_day, planet_id, nodbit, calc_iflag)
                    # result is a tuple of 4 elements, each a 6-element array:
                    # [0] ascending node, [1] descending node, [2] perihelion, [3] aphelion
                    asc_lon = (result[0][0] - ayanamsa) % 360
                    desc_lon = (result[1][0] - ayanamsa) % 360
                    peri_lon = (result[2][0] - ayanamsa) % 360
                    aph_lon = (result[3][0] - ayanamsa) % 360

                    node_results.append(PlanetaryNodeModel(
                        planet_name=name,
                        ascending_node=get_kerykeion_point_from_degree(
                            asc_lon, name, "AstrologicalPoint"
                        ),
                        descending_node=get_kerykeion_point_from_degree(
                            desc_lon, name, "AstrologicalPoint"
                        ),
                        perihelion=get_kerykeion_point_from_degree(
                            peri_lon, name, "AstrologicalPoint"
                        ),
                        aphelion=get_kerykeion_point_from_degree(
                            aph_lon, name, "AstrologicalPoint"
                        ),
                    ))
                except Exception as e:
                    logger.warning(f"Could not calculate nodes for {name}: {e}")

        # Tolerate individual-planet failures, but surface the all-failed case
        # (otherwise an empty result is indistinguishable from a valid "no nodes").
        if target_planets and not node_results:
            raise KerykeionException(
                "Failed to calculate planetary nodes for all requested planets "
                f"({', '.join(target_planets)}); the ephemeris backend may have "
                "changed or be unavailable. See logs for per-planet errors."
            )

        return PlanetaryNodesCollectionModel(
            iso_datetime=iso_datetime,
            julian_day=julian_day,
            method=method,
            nodes=node_results,
        )
