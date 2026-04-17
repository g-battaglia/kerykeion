# -*- coding: utf-8 -*-
"""Calculate planetary nodes and apsides for any planet.

For each planet, computes:
- Ascending node: where the orbit crosses the ecliptic northward
- Descending node: where the orbit crosses southward
- Perihelion: closest point to the Sun
- Aphelion: farthest point from the Sun

Swiss Ephemeris function: swe.nod_aps_ut(jd_ut, planet, iflag, method)
Methods: NODBIT_MEAN (mean elements), NODBIT_OSCU (osculating/instantaneous)
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

from kerykeion.ephemeris_backend import swe, EPHE_DATA_PATH

from kerykeion.schemas.kr_models import (
    AstrologicalSubjectModel,
    KerykeionPointModel,
    SubscriptableBaseModel,
)
from kerykeion.utilities import get_kerykeion_point_from_degree
from pydantic import Field

logger = logging.getLogger(__name__)

_EPHE_PATH = EPHE_DATA_PATH

NODBIT_MEAN = getattr(swe, "NODBIT_MEAN", 1)
NODBIT_OSCU = getattr(swe, "NODBIT_OSCU", 2)

_NODE_PLANETS: Dict[str, int] = {
    "Sun": swe.SUN,
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
    """Calculate planetary nodes and apsides."""

    @staticmethod
    def from_subject(
        subject: AstrologicalSubjectModel,
        method: str = "mean",
        planets: Optional[List[str]] = None,
    ) -> PlanetaryNodesCollectionModel:
        """Calculate nodes from an existing astrological subject.

        Args:
            subject: An astrological subject.
            method: "mean" or "osculating".
            planets: Optional list of planet names. Defaults to all.
        """
        return PlanetaryNodesFactory._calculate(
            julian_day=subject.julian_day,
            iso_datetime=subject.iso_formatted_utc_datetime,
            method=method,
            planets=planets,
        )

    @staticmethod
    def from_julian_day(
        julian_day: float,
        method: str = "mean",
        planets: Optional[List[str]] = None,
    ) -> PlanetaryNodesCollectionModel:
        """Calculate nodes from a Julian Day number."""
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
    ) -> PlanetaryNodesCollectionModel:
        swe.set_ephe_path(_EPHE_PATH)
        iflag = swe.FLG_SWIEPH | swe.FLG_SPEED
        nodbit = NODBIT_MEAN if method == "mean" else NODBIT_OSCU

        target_planets = _NODE_PLANETS if planets is None else {
            k: v for k, v in _NODE_PLANETS.items() if k in planets
        }

        node_results: List[PlanetaryNodeModel] = []

        for name, planet_id in target_planets.items():
            try:
                result = swe.nod_aps_ut(julian_day, planet_id, iflag, nodbit)
                # result is a tuple of 4 elements, each a 6-element array:
                # [0] ascending node, [1] descending node, [2] perihelion, [3] aphelion
                asc_lon = result[0][0] % 360
                desc_lon = result[1][0] % 360
                peri_lon = result[2][0] % 360
                aph_lon = result[3][0] % 360

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

        swe.close()
        return PlanetaryNodesCollectionModel(
            iso_datetime=iso_datetime,
            julian_day=julian_day,
            method=method,
            nodes=node_results,
        )
