# -*- coding: utf-8 -*-
"""
Fixed Star Discovery Factory (v6.0)

Finds fixed stars conjunct natal points within a configurable orb.

The implementation is backend-specific by design:
- swisseph scans the Swiss Ephemeris ``sefstars.txt`` catalog.
- libephemeris uses its native fixed-star catalog/API and never reads
  ``sefstars.txt``.

This is part of Kerykeion (C) 2025 Giacomo Battaglia
"""

from functools import lru_cache
import logging
from pathlib import Path
from typing import Optional

from kerykeion.ephemeris_backend import BACKEND_NAME, EPHE_DATA_PATH, swe
from kerykeion.schemas.kr_models import AstrologicalSubjectModel, KerykeionPointModel
from kerykeion.utilities import get_kerykeion_point_from_degree, get_planet_house

logger = logging.getLogger(__name__)


@lru_cache(maxsize=8)
def _parse_star_names_from_catalog(catalog_path: str) -> tuple[str, ...]:
    """Parse primary star names from a Swiss Ephemeris sefstars.txt file."""
    names: list[str] = []
    try:
        with open(catalog_path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                # sefstars.txt format: "name, nomenclature, equinox, RA, Dec, ..."
                name = line.split(",")[0].strip()
                if name:
                    names.append(name)
    except Exception as e:
        logger.warning(f"Could not parse star catalog: {e}")
    return tuple(names)


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
    """Factory for discovering fixed-star conjunctions in a chart."""

    @staticmethod
    def find_prominent_stars(
        subject: AstrologicalSubjectModel,
        orb: float = 1.0,
        *,
        catalog_path: Optional[str] = None,
    ) -> list[KerykeionPointModel]:
        """Find fixed stars conjunct natal planets.

        The active backend determines the catalog source. The Swiss Ephemeris
        backend reads ``sefstars.txt``; libephemeris uses its own native catalog.
        """
        if BACKEND_NAME == "swisseph":
            return FixedStarDiscoveryFactory._find_prominent_stars_swisseph(subject, orb=orb, catalog_path=catalog_path)
        if BACKEND_NAME == "libephemeris":
            if catalog_path is not None:
                logger.warning("catalog_path is ignored with the libephemeris backend (uses its own native catalog)")
            return FixedStarDiscoveryFactory._find_prominent_stars_libephemeris(subject, orb=orb)
        raise RuntimeError(f"Unsupported ephemeris backend for fixed-star discovery: {BACKEND_NAME}")

    @staticmethod
    def _find_prominent_stars_swisseph(
        subject: AstrologicalSubjectModel,
        orb: float = 1.0,
        *,
        catalog_path: Optional[str] = None,
    ) -> list[KerykeionPointModel]:
        """Swiss Ephemeris implementation backed by sefstars.txt."""
        if catalog_path is None:
            catalog_path = str(Path(EPHE_DATA_PATH) / "sefstars.txt")

        star_names = _parse_star_names_from_catalog(catalog_path)
        if not star_names:
            logger.warning("No star names found in catalog")
            return []

        planet_positions = _collect_planet_positions(subject)
        if not planet_positions:
            return []

        houses_degree_ut = _collect_house_cusps(subject)
        swe.set_ephe_path(EPHE_DATA_PATH)
        scan_iflag = swe.FLG_SWIEPH | swe.FLG_SPEED
        jd = subject.julian_day

        prominent: list[KerykeionPointModel] = []
        seen_positions: set[float] = set()
        try:
            for star_name in star_names:
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
                    try:
                        star_mag = swe.fixstar2_mag(star_name)[0]
                    except Exception:
                        star_mag = None

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
                except Exception:
                    continue
        finally:
            swe.close()

        prominent.sort(key=lambda p: p.magnitude if p.magnitude is not None else 99)
        return prominent

    @staticmethod
    def _find_prominent_stars_libephemeris(
        subject: AstrologicalSubjectModel,
        orb: float = 1.0,
    ) -> list[KerykeionPointModel]:
        """libephemeris implementation backed by its native catalog/API."""
        planet_positions = _collect_planet_positions(subject)
        if not planet_positions:
            return []

        list_fixed_stars = getattr(swe, "list_fixed_stars", None)
        batch_fixstars_ut = getattr(swe, "batch_fixstars_ut", None)
        if list_fixed_stars is None or batch_fixstars_ut is None:
            raise RuntimeError("libephemeris fixed-star discovery requires libephemeris >= 1.2.0")

        catalog = tuple(list_fixed_stars())
        if not catalog:
            return []

        houses_degree_ut = _collect_house_cusps(subject)
        swe.set_ephe_path(EPHE_DATA_PATH)
        base_iflag = swe.FLG_SWIEPH
        jd = subject.julian_day
        star_names = tuple(star.name for star in catalog)

        prominent: list[KerykeionPointModel] = []
        seen_positions: set[float] = set()
        try:
            scanned_positions = batch_fixstars_ut(star_names, jd, base_iflag, skip_errors=True)

            for catalog_entry, scan_result in zip(catalog, scanned_positions):
                if scan_result is None:
                    continue
                star_name = scan_result[1] or catalog_entry.name
                pos_scan = scan_result[0]
                star_deg = pos_scan[0]

                nearest = _nearest_conjunction(star_deg, planet_positions, orb)
                if nearest is None:
                    continue

                rounded_pos = round(star_deg, 2)
                if rounded_pos in seen_positions:
                    continue
                seen_positions.add(rounded_pos)

                try:
                    pos_ecl = swe.fixstar_ut(star_name, jd, base_iflag | swe.FLG_SPEED)[0]
                    pos_eq = swe.fixstar_ut(star_name, jd, base_iflag | swe.FLG_EQUATORIAL)[0]
                except Exception:
                    continue

                prominent.append(
                    _build_discovery_point(
                        star_name,
                        pos_ecl,
                        pos_eq,
                        catalog_entry.magnitude,
                        houses_degree_ut,
                        near_point=nearest[0],
                        discovery_orb=nearest[1],
                    )
                )
        finally:
            reset = getattr(swe, "reset_session", None) or swe.close
            reset()

        prominent.sort(key=lambda p: p.magnitude if p.magnitude is not None else 99)
        return prominent
