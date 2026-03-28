# -*- coding: utf-8 -*-
"""
Occultation Factory Module

This module provides the OccultationFactory class for searching lunar
occultations -- events where the Moon passes in front of a planet or star
as seen from Earth.

It wraps the Swiss Ephemeris functions ``swe.lun_occult_when_glob`` (global
search) and ``swe.lun_occult_when_loc`` (location-specific search) and
returns structured Pydantic models.

Classes:
    OccultationFactory: Find upcoming (or past) lunar occultation events.
    OccultationModel: Pydantic model describing a single occultation event.

Example:
    >>> import swisseph as swe
    >>> from kerykeion.occultations import OccultationFactory
    >>>
    >>> jd = swe.julday(2024, 1, 1, 0.0)
    >>> factory = OccultationFactory()
    >>> results = factory.search_global(jd, swe.VENUS, count=3)
    >>> for occ in results:
    ...     print(occ.planet_name, occ.type, occ.datestamp)

Author: Giacomo Battaglia
Copyright: (C) 2025 Kerykeion Project
License: AGPL-3.0
"""

import logging
import swisseph as swe

from pathlib import Path
from pydantic import Field
from typing import List

from kerykeion.schemas.kr_models import SubscriptableBaseModel

# Set ephemeris path at module load
swe.set_ephe_path(str(Path(__file__).parent.parent / "sweph"))

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Occultation type flag-to-label mapping
# ---------------------------------------------------------------------------

_ECL_TYPE_LABELS = {
    getattr(swe, "ECL_TOTAL", 1): "Total",
    getattr(swe, "ECL_ANNULAR", 2): "Annular",
    getattr(swe, "ECL_PARTIAL", 4): "Partial",
}


def _classify_occultation(retflags: int) -> str:
    """Return a human-readable label for the occultation type flags."""
    for flag, label in _ECL_TYPE_LABELS.items():
        if retflags & flag:
            return label
    return "Unknown"


def _jd_to_iso(jd: float) -> str:
    """Convert a Julian Day to an ISO-8601 UTC timestamp string."""
    year, month, day, hour_frac = swe.revjul(jd)
    hh = int(hour_frac)
    rest = (hour_frac - hh) * 60
    mm = int(rest)
    ss = int((rest - mm) * 60)
    return f"{year:04d}-{month:02d}-{day:02d}T{hh:02d}:{mm:02d}:{ss:02d}Z"


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


class OccultationModel(SubscriptableBaseModel):
    """Describes a single lunar occultation event.

    Attributes:
        planet_name: Name of the occulted body (e.g. ``"Venus"``).
        type: Human-readable occultation type (``"Total"``, ``"Partial"``, etc.).
        maximum_jd: Julian Day of the moment of maximum occultation.
        datestamp: ISO-8601 UTC string of the maximum moment.
    """

    planet_name: str = Field(..., description="Name of the occulted body")
    type: str = Field(..., description="Occultation type (Total, Partial, ...)")
    maximum_jd: float = Field(..., description="Julian Day of maximum occultation")
    datestamp: str = Field(..., description="ISO-8601 UTC datestamp of maximum")


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


class OccultationFactory:
    """Search for lunar occultation events using the Swiss Ephemeris.

    The factory is stateless -- each search method takes the required inputs
    and returns a list of :class:`OccultationModel` instances.

    Example::

        factory = OccultationFactory()
        events = factory.search_global(jd_start, swe.SATURN, count=5)
    """

    # ------------------------------------------------------------------
    # Global search
    # ------------------------------------------------------------------

    def search_global(
        self,
        julian_day: float,
        planet_id: int,
        count: int = 5,
    ) -> List[OccultationModel]:
        """Find the next *count* global lunar occultations of *planet_id*.

        A global search answers the question "when does an occultation of
        this body happen *anywhere* on Earth?"

        Args:
            julian_day: Starting Julian Day (UT) for the search.
            planet_id: Swiss Ephemeris planet identifier (e.g. ``swe.VENUS``).
            count: Number of events to return. Defaults to ``5``.

        Returns:
            A list of :class:`OccultationModel` instances ordered by date.
        """
        planet_name = swe.get_planet_name(planet_id)
        results: List[OccultationModel] = []
        cursor = julian_day

        for _ in range(count):
            try:
                retflags, tret = swe.lun_occult_when_glob(
                    cursor,
                    planet_id,
                    swe.FLG_SWIEPH,
                    0,
                    False,
                )
            except Exception:
                logger.warning(
                    "swe.lun_occult_when_glob raised an exception; stopping search.",
                    exc_info=True,
                )
                break

            if retflags == 0 or tret[0] == 0.0:
                break

            max_jd = tret[0]
            results.append(
                OccultationModel(
                    planet_name=planet_name,
                    type=_classify_occultation(retflags),
                    maximum_jd=max_jd,
                    datestamp=_jd_to_iso(max_jd),
                )
            )
            # Advance past this event for the next iteration.
            cursor = max_jd + 1.0

        return results

    # ------------------------------------------------------------------
    # Local search
    # ------------------------------------------------------------------

    def search_local(
        self,
        julian_day: float,
        planet_id: int,
        lat: float,
        lng: float,
        count: int = 5,
    ) -> List[OccultationModel]:
        """Find the next *count* lunar occultations visible from a location.

        A local search answers the question "when is an occultation of this
        body visible from *this* place on Earth?"

        Args:
            julian_day: Starting Julian Day (UT) for the search.
            planet_id: Swiss Ephemeris planet identifier (e.g. ``swe.MARS``).
            lat: Geographic latitude (northern positive).
            lng: Geographic longitude (eastern positive).
            count: Number of events to return. Defaults to ``5``.

        Returns:
            A list of :class:`OccultationModel` instances ordered by date.
        """
        planet_name = swe.get_planet_name(planet_id)
        geopos = (lng, lat, 0.0)  # (longitude, latitude, altitude)
        results: List[OccultationModel] = []
        cursor = julian_day

        for _ in range(count):
            try:
                retflags, tret, _attr = swe.lun_occult_when_loc(
                    cursor,
                    planet_id,
                    geopos,
                    swe.FLG_SWIEPH,
                    False,
                )
            except Exception:
                logger.warning(
                    "swe.lun_occult_when_loc raised an exception; stopping search.",
                    exc_info=True,
                )
                break

            if retflags == 0 or tret[0] == 0.0:
                break

            max_jd = tret[0]
            results.append(
                OccultationModel(
                    planet_name=planet_name,
                    type=_classify_occultation(retflags),
                    maximum_jd=max_jd,
                    datestamp=_jd_to_iso(max_jd),
                )
            )
            # Advance past this event for the next iteration.
            cursor = max_jd + 1.0

        return results
