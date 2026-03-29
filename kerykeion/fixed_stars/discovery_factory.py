# -*- coding: utf-8 -*-
"""
Fixed Star Discovery Factory (v6.0)

Scans the Swiss Ephemeris sefstars.txt catalog and finds fixed stars
that are conjunct natal planets within a configurable orb.

This is part of Kerykeion (C) 2025 Giacomo Battaglia
"""

import logging
from kerykeion.ephemeris_backend import swe, EPHE_DATA_PATH
from pathlib import Path
from typing import List, Optional

from kerykeion.schemas.kr_models import AstrologicalSubjectModel, KerykeionPointModel
from kerykeion.utilities import get_kerykeion_point_from_degree, get_planet_house

logger = logging.getLogger(__name__)


def _parse_star_names_from_catalog(catalog_path: str) -> List[str]:
    """Parse star names from the sefstars.txt catalog file.

    Returns a list of primary star names (the first name before any comma
    on each non-comment, non-empty line).
    """
    names: List[str] = []
    try:
        with open(catalog_path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                # sefstars.txt format: "name, nomenclature, equinox, RA, Dec, ..."
                # The first field (before the first comma) is the star name
                name = line.split(",")[0].strip()
                if name:
                    names.append(name)
    except Exception as e:
        logger.warning(f"Could not parse star catalog: {e}")
    return names


class FixedStarDiscoveryFactory:
    """
    Factory for discovering prominent fixed stars in an astrological chart.

    Scans the Swiss Ephemeris fixed star catalog (~1000 stars) and returns
    those that form a conjunction with any natal planet within the specified orb.

    Example:
        >>> subject = AstrologicalSubjectFactory.from_birth_data("John", 1940, 10, 9, 18, 30, "Liverpool", "GB")
        >>> prominent = FixedStarDiscoveryFactory.find_prominent_stars(subject, orb=1.0)
        >>> for star in prominent:
        ...     print(f"{star.name} at {star.abs_pos:.2f} (mag {star.magnitude})")
    """

    @staticmethod
    def find_prominent_stars(
        subject: AstrologicalSubjectModel,
        orb: float = 1.0,
        *,
        catalog_path: Optional[str] = None,
    ) -> List[KerykeionPointModel]:
        """
        Find fixed stars conjunct natal planets.

        Scans the full sefstars.txt catalog and returns stars whose ecliptic
        longitude is within *orb* degrees of any calculated planet in the subject.

        Args:
            subject: An astrological subject with calculated planet positions.
            orb: Maximum orb in degrees for conjunction (default 1.0).
            catalog_path: Optional path to sefstars.txt. If None, uses the
                bundled catalog.

        Returns:
            List of KerykeionPointModel for each prominent star found.
        """
        if catalog_path is None:
            catalog_path = str(Path(EPHE_DATA_PATH) / "sefstars.txt")

        star_names = _parse_star_names_from_catalog(catalog_path)
        if not star_names:
            logger.warning("No star names found in catalog")
            return []

        # Collect natal planet positions for conjunction check
        planet_positions: List[float] = []
        for point_name in subject.active_points:
            point = subject.get(point_name.lower())
            if point is not None and hasattr(point, "abs_pos"):
                planet_positions.append(point.abs_pos)

        if not planet_positions:
            return []

        # Get house cusps for house placement
        houses_degree_ut: List[float] = []
        for i in range(1, 13):
            house_key = [
                "first_house", "second_house", "third_house", "fourth_house",
                "fifth_house", "sixth_house", "seventh_house", "eighth_house",
                "ninth_house", "tenth_house", "eleventh_house", "twelfth_house",
            ][i - 1]
            h = getattr(subject, house_key, None)
            if h is not None:
                houses_degree_ut.append(h.abs_pos)

        # Setup ephemeris
        ephe_path = EPHE_DATA_PATH
        swe.set_ephe_path(ephe_path)
        iflag = swe.FLG_SWIEPH | swe.FLG_SPEED
        jd = subject.julian_day

        prominent: List[KerykeionPointModel] = []
        seen_names: set = set()

        for star_name in star_names:
            try:
                pos_ecl = swe.fixstar_ut(star_name, jd, iflag)[0]
                star_deg = pos_ecl[0]

                # Check conjunction with any natal planet
                is_conjunct = False
                for planet_pos in planet_positions:
                    diff = abs(star_deg - planet_pos)
                    if diff > 180:
                        diff = 360 - diff
                    if diff <= orb:
                        is_conjunct = True
                        break

                if not is_conjunct:
                    continue

                # Avoid duplicates (catalog may have alternate names)
                rounded_pos = round(star_deg, 2)
                if rounded_pos in seen_names:
                    continue
                seen_names.add(rounded_pos)

                # Full calculation
                star_speed = pos_ecl[3] if len(pos_ecl) > 3 else 0.0
                pos_eq = swe.fixstar_ut(star_name, jd, iflag | swe.FLG_EQUATORIAL)[0]
                star_dec = pos_eq[1] if len(pos_eq) > 1 else None

                try:
                    star_mag = swe.fixstar2_mag(star_name)[0]
                except Exception:
                    star_mag = None

                point = get_kerykeion_point_from_degree(
                    star_deg, star_name, point_type="AstrologicalPoint",
                    speed=star_speed, declination=star_dec, magnitude=star_mag,
                )
                if houses_degree_ut:
                    point.house = get_planet_house(star_deg, houses_degree_ut)
                point.retrograde = False

                prominent.append(point)

            except Exception:
                # Star not found or calculation error — skip silently
                continue

        swe.close()

        # Sort by magnitude (brightest first), None magnitudes last
        prominent.sort(key=lambda p: p.magnitude if p.magnitude is not None else 99)
        return prominent
