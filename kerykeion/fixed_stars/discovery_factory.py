# -*- coding: utf-8 -*-
"""
Fixed Star Discovery Factory (v6)

Finds fixed stars conjunct natal points within a configurable orb.

The catalog is sourced from ``libephemeris`` (``list_fixed_stars()``);
``sefstars.txt`` is NOT used for licensing reasons. Position calculations
still go through the active ephemeris backend (``swe.fixstar_ut``), which
on libephemeris uses its own internal data and on swisseph requires a
locally-installed ``sefstars.txt`` (only relevant for users who manage
their own catalog).

This is part of Kerykeion (C) 2025 Giacomo Battaglia
"""

from __future__ import annotations

import logging

from kerykeion.ephemeris_backend import BACKEND_NAME, EPHE_DATA_PATH, swe
from kerykeion.fixed_stars.catalog import FixedStarCatalog
from kerykeion.schemas.kr_models import AstrologicalSubjectModel, KerykeionPointModel
from kerykeion.utilities import get_kerykeion_point_from_degree, get_planet_house

logger = logging.getLogger(__name__)


def _collect_planet_positions(subject: AstrologicalSubjectModel) -> list[tuple[str, float]]:
    """Collect calculated active point positions for conjunction checks."""
    planet_positions: list[tuple[str, float]] = []
    for point_name in subject.active_points:
        point = subject.get(point_name.lower())
        if point is not None and hasattr(point, "abs_pos"):
            planet_positions.append((str(point_name), point.abs_pos))
    return planet_positions


def _collect_house_cusps(subject: AstrologicalSubjectModel) -> list[float]:
    """Collect house cusp longitudes for house placement."""
    houses_degree_ut: list[float] = []
    house_keys = [
        "first_house",
        "second_house",
        "third_house",
        "fourth_house",
        "fifth_house",
        "sixth_house",
        "seventh_house",
        "eighth_house",
        "ninth_house",
        "tenth_house",
        "eleventh_house",
        "twelfth_house",
    ]
    for house_key in house_keys:
        house = getattr(subject, house_key, None)
        if house is not None:
            houses_degree_ut.append(house.abs_pos)
    return houses_degree_ut


def _nearest_conjunction(
    star_deg: float,
    planet_positions: list[tuple[str, float]],
    orb: float,
) -> tuple[str, float] | None:
    """Return nearest conjunct point and orb, or None when outside orb."""
    nearest: tuple[str, float] | None = None
    for point_name, planet_pos in planet_positions:
        diff = abs(star_deg - planet_pos)
        if diff > 180:
            diff = 360 - diff
        if diff <= orb and (nearest is None or diff < nearest[1]):
            nearest = (point_name, diff)
    return nearest


def _build_discovery_point(
    star_name: str,
    pos_ecl: tuple,
    pos_eq: tuple | None,
    star_mag: float | None,
    houses_degree_ut: list[float],
    near_point: str,
    discovery_orb: float,
) -> KerykeionPointModel:
    """Build a Kerykeion point enriched with discovery metadata."""
    star_deg = pos_ecl[0]
    star_lat = pos_ecl[1] if len(pos_ecl) > 1 else None
    star_speed = pos_ecl[3] if len(pos_ecl) > 3 else 0.0
    star_dec = pos_eq[1] if pos_eq is not None and len(pos_eq) > 1 else None

    point = get_kerykeion_point_from_degree(
        star_deg,
        star_name,
        point_type="AstrologicalPoint",
        speed=star_speed,
        declination=star_dec,
        magnitude=star_mag,
    )
    if houses_degree_ut:
        point.house = get_planet_house(star_deg, houses_degree_ut)
    point.retrograde = False
    point.near_point = near_point
    point.orb = discovery_orb
    point.aspect = "conjunction"
    point.longitude = star_deg
    point.latitude = star_lat
    point.degree = point.position
    return point


class FixedStarDiscoveryFactory:
    """Factory for discovering fixed-star conjunctions in a chart.

    Catalog source is ``libephemeris`` (single source of truth, v6).
    """

    @staticmethod
    def find_prominent_stars(
        subject: AstrologicalSubjectModel,
        orb: float = 1.0,
    ) -> list[KerykeionPointModel]:
        """Find fixed stars conjunct natal planets within ``orb`` degrees.

        Returns a list of KerykeionPointModel sorted by magnitude (brightest first).
        Only stars that are within ``orb`` degrees of any natal planet are included.
        """
        if orb < 0:
            raise ValueError(f"orb must be >= 0, got {orb}")

        planet_positions = _collect_planet_positions(subject)
        if not planet_positions:
            return []

        catalog = FixedStarCatalog.list_all()
        if not catalog:
            return []

        houses_degree_ut = _collect_house_cusps(subject)
        swe.set_ephe_path(EPHE_DATA_PATH)
        scan_iflag = swe.FLG_SWIEPH | swe.FLG_SPEED
        jd = subject.julian_day

        prominent: list[KerykeionPointModel] = []
        seen_positions: set[float] = set()
        try:
            for entry in catalog:
                star_name = entry.name
                try:
                    pos_ecl = swe.fixstar_ut(star_name, jd, scan_iflag)[0]
                    star_deg = pos_ecl[0]

                    nearest = _nearest_conjunction(star_deg, planet_positions, orb)
                    if nearest is None:
                        continue

                    rounded_pos = round(star_deg, 2)
                    if rounded_pos in seen_positions:
                        continue
                    seen_positions.add(rounded_pos)

                    pos_eq = swe.fixstar_ut(star_name, jd, scan_iflag | swe.FLG_EQUATORIAL)[0]
                    star_mag = entry.magnitude

                    prominent.append(
                        _build_discovery_point(
                            star_name,
                            pos_ecl,
                            pos_eq,
                            star_mag,
                            houses_degree_ut,
                            near_point=nearest[0],
                            discovery_orb=nearest[1],
                        )
                    )
                except Exception as e:
                    logger.debug(f"Skipping star {star_name}: {e}")
                    continue
        finally:
            reset = getattr(swe, "reset_session", None) or swe.close
            reset()

        # v6: emit a single actionable warning when nothing was returned on
        # the swisseph backend — almost always means sefstars.txt is missing
        # from KERYKEION_EPHE_PATH. See site/docs/swisseph_configuration.md.
        if not prominent and BACKEND_NAME == "swisseph":
            logger.warning(
                "FixedStarDiscoveryFactory found no stars on the swisseph backend. "
                "The catalog file 'sefstars.txt' is not bundled with kerykeion due "
                "to licensing. Download it from "
                "https://github.com/aloistr/swisseph/tree/master/ephe and place it "
                "in KERYKEION_EPHE_PATH (%s). Alternatively use "
                "KERYKEION_BACKEND=libephemeris (ships its own catalog).",
                EPHE_DATA_PATH or "<unset>",
            )

        prominent.sort(key=lambda p: p.magnitude if p.magnitude is not None else 99)
        return prominent
