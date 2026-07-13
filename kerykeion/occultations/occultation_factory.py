# -*- coding: utf-8 -*-
"""
Occultation Factory Module

This module provides the OccultationFactory class for searching lunar
occultations -- events where the Moon passes in front of a planet or star
as seen from Earth.

It wraps the Swiss Ephemeris functions ``ephe.lun_occult_when_glob`` (global
search) and ``ephe.lun_occult_when_loc`` (location-specific search) and
returns structured Pydantic models.

Classes:
    OccultationFactory: Find upcoming (or past) lunar occultation events.
    OccultationModel: Pydantic model describing a single occultation event.

Example:
    >>> from kerykeion.ephemeris_backend import ephe
    >>> from kerykeion.occultations import OccultationFactory
    >>>
    >>> jd = ephe.julday(2024, 1, 1, 0.0)
    >>> factory = OccultationFactory()
    >>> results = factory.search_global(jd, ephe.VENUS, count=3)
    >>> for occ in results:
    ...     print(occ.planet_name, occ.type, occ.datestamp)

Author: Giacomo Battaglia
Copyright: (C) 2025 Kerykeion Project
License: AGPL-3.0
"""

import logging
from kerykeion.ephemeris_backend import ephe, ephemeris_session
from kerykeion._predictive_utils import jd_to_iso_utc as _jd_to_iso, validate_julian_day
from kerykeion.settings.config_constants import STANDARD_PLANETS

from pydantic import Field
from typing import List, Union, cast

from kerykeion.schemas.kerykeion_exception import KerykeionException
from kerykeion.schemas.kr_literals import AstrologicalPoint
from kerykeion.schemas.kr_models import SubscriptableBaseModel
from kerykeion.utilities import validate_latitude, validate_longitude

logger = logging.getLogger(__name__)

# Backstop on events per search. Each event is found with a single backend
# call, so this still allows centuries of coverage; absurd requests are
# rejected upfront (like the eclipse factory's ``_ensure_scannable``) rather
# than left to fail mid-scan or silently truncate.
_MAX_COUNT = 1_000

# ---------------------------------------------------------------------------
# Occultation type flag-to-label mapping
# ---------------------------------------------------------------------------

_ECL_TYPE_LABELS = {
    getattr(ephe, "ECL_TOTAL", 4): "Total",
    getattr(ephe, "ECL_ANNULAR", 8): "Annular",
    getattr(ephe, "ECL_PARTIAL", 16): "Partial",
}


def _classify_occultation(retflags: int) -> str:
    """Return a human-readable label for the occultation type flags."""
    for flag, label in _ECL_TYPE_LABELS.items():
        if retflags & flag:
            return label
    return "Unknown"



def _ensure_scannable(count: int) -> None:
    """Reject absurd event counts upfront, so a caller never receives a
    silently truncated result and never waits on a scan that cannot finish."""
    if count < 0:
        raise ValueError("count must be non-negative")
    if count > _MAX_COUNT:
        raise ValueError(
            f"count too large (> {_MAX_COUNT} events per search). "
            f"Request fewer events per search."
        )


# Only physically real bodies can be occulted by the Moon. STANDARD_PLANETS also
# contains calculated points (lunar nodes, Lilith/apogee variants, the Uranian
# hypotheticals) and the Moon/Earth themselves; feeding those to the backend's
# lun_occult primitive fabricates a plausible-looking but meaningless "occultation"
# of a point that has no disk to be covered. Restrict string names to the real
# occultable bodies (the classical planets plus the resolvable minor planets).
_OCCULTABLE_BODY_NAMES = frozenset({
    "Sun", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto",
    "Chiron", "Pholus", "Ceres", "Pallas", "Juno", "Vesta",
})
_OCCULTABLE_BODY_IDS = frozenset(STANDARD_PLANETS[cast(AstrologicalPoint, name)] for name in _OCCULTABLE_BODY_NAMES)


def _resolve_planet_id(planet_id: Union[int, str]) -> int:
    """Resolve *planet_id* to a Swiss Ephemeris body number.

    Raw backend IDs (``int``, e.g. ``ephe.VENUS``) stay supported; a planet
    name (``str``, e.g. ``"Venus"``) is resolved through the project-wide
    name -> ID map (``STANDARD_PLANETS`` in ``settings.config_constants``),
    matching PlanetaryReturnFactory's name handling, then restricted to the
    physically occultable bodies (:data:`_OCCULTABLE_BODY_NAMES`).

    Raises:
        KerykeionException: If the name is not a known planet, or is a known
            name that is not a physically occultable body (a calculated point
            such as a lunar node, Lilith, or a Uranian hypothetical).
        TypeError: If *planet_id* is neither an int nor a str.
    """
    if isinstance(planet_id, str):
        resolved = STANDARD_PLANETS.get(cast(AstrologicalPoint, planet_id))
        if resolved is None:
            raise KerykeionException(
                f"Unknown planet name for occultation search: {planet_id!r}. "
                f"Valid names: {', '.join(sorted(_OCCULTABLE_BODY_NAMES))}."
            )
        if planet_id not in _OCCULTABLE_BODY_NAMES:
            raise KerykeionException(
                f"{planet_id!r} is not a physically occultable body (it is a "
                f"calculated point). Occultation search accepts: "
                f"{', '.join(sorted(_OCCULTABLE_BODY_NAMES))}."
            )
        return resolved
    if isinstance(planet_id, int) and not isinstance(planet_id, bool):
        if planet_id not in _OCCULTABLE_BODY_IDS:
            raise KerykeionException(
                f"Swiss Ephemeris body ID {planet_id} is not a physically occultable body. "
                f"Occultation search accepts IDs for: {', '.join(sorted(_OCCULTABLE_BODY_NAMES))}."
            )
        return planet_id
    raise TypeError(
        f"planet_id must be a Swiss Ephemeris body number (int) or a planet "
        f"name (str), got {type(planet_id).__name__}."
    )


def _search_failure(kind: str, jd: float, exc: Exception) -> KerykeionException:
    """Build the exception raised when the backend fails mid-scan.

    A failing occultation primitive call must abort the search: logging and
    returning the events found so far would silently truncate a result that
    still claims full coverage. The most common cause is a search that walked
    past the edge of the available ephemeris data.
    """
    return KerykeionException(
        f"{kind} occultation search failed at JD {jd:.5f}: {exc}. "
        f"This usually means the search reached a date outside the available "
        f"ephemeris range; use a julian_day/count combination covered by the "
        f"installed ephemeris data."
    )


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
        events = factory.search_global(jd_start, ephe.SATURN, count=5)
    """

    # ------------------------------------------------------------------
    # Global search
    # ------------------------------------------------------------------

    def search_global(
        self,
        julian_day: float,
        planet_id: Union[int, str],
        count: int = 5,
    ) -> List[OccultationModel]:
        """Find the next *count* global lunar occultations of *planet_id*.

        A global search answers the question "when does an occultation of
        this body happen *anywhere* on Earth?"

        Args:
            julian_day: Starting Julian Day (UT) for the search.
            planet_id: Swiss Ephemeris planet identifier (e.g. ``ephe.VENUS``)
                or planet name (e.g. ``"Venus"``).
            count: Number of events to return. Defaults to ``5``.

        Returns:
            A list of :class:`OccultationModel` instances ordered by date.

        Raises:
            KerykeionException: If the planet name is unknown, or if the
                ephemeris backend fails mid-search (most often a date outside
                the available ephemeris range); the search never returns
                silently truncated results.
            ValueError: If ``count`` is negative or exceeds the supported maximum.
        """
        validate_julian_day(julian_day)
        _ensure_scannable(count)
        planet_id = _resolve_planet_id(planet_id)
        planet_name = ephe.get_planet_name(planet_id)
        results: List[OccultationModel] = []
        cursor = julian_day

        with ephemeris_session():
            for _ in range(count):
                try:
                    retflags, tret = ephe.lun_occult_when_glob(
                        cursor,
                        planet_id,
                        ephe.FLG_SWIEPH,
                        0,
                        False,
                    )
                except Exception as exc:
                    raise _search_failure("Global", cursor, exc) from exc

                if retflags == 0 or tret[0] == 0.0:
                    # retflags == 0 means "no further occultation of this
                    # body" -- a legitimate terminal result, not an error.
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
        planet_id: Union[int, str],
        lat: float,
        lng: float,
        count: int = 5,
    ) -> List[OccultationModel]:
        """Find the next *count* lunar occultations visible from a location.

        A local search answers the question "when is an occultation of this
        body visible from *this* place on Earth?"

        Args:
            julian_day: Starting Julian Day (UT) for the search.
            planet_id: Swiss Ephemeris planet identifier (e.g. ``ephe.MARS``)
                or planet name (e.g. ``"Mars"``).
            lat: Geographic latitude (northern positive).
            lng: Geographic longitude (eastern positive).
            count: Number of events to return. Defaults to ``5``.

        Returns:
            A list of :class:`OccultationModel` instances ordered by date.

        Raises:
            KerykeionException: If the planet name is unknown or not a physically
                occultable body, if ``lat`` is outside the geometrically-possible
                ±90° range, if ``lng`` is outside ±180°, or if the ephemeris backend fails mid-search (most
                often a date outside the available ephemeris range); the search
                never returns silently truncated results.
            ValueError: If ``count`` is negative or exceeds the supported maximum.
        """
        validate_julian_day(julian_day)
        _ensure_scannable(count)
        # Reject an impossible latitude (e.g. an accidental lat/lng swap, made
        # easy by the longitude-first backend geopos convention) rather than
        # returning a bogus "visible" occultation.
        validate_latitude(lat)
        validate_longitude(lng)
        planet_id = _resolve_planet_id(planet_id)
        planet_name = ephe.get_planet_name(planet_id)
        geopos = (lng, lat, 0.0)  # (longitude, latitude, altitude)
        results: List[OccultationModel] = []
        cursor = julian_day

        with ephemeris_session():
            for _ in range(count):
                try:
                    retflags, tret, _attr = ephe.lun_occult_when_loc(
                        cursor,
                        planet_id,
                        geopos,
                        ephe.FLG_SWIEPH,
                        False,
                    )
                except Exception as exc:
                    raise _search_failure("Local", cursor, exc) from exc

                if retflags == 0 or tret[0] == 0.0:
                    # retflags == 0 means "no further occultation of this
                    # body" -- a legitimate terminal result, not an error.
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
