# -*- coding: utf-8 -*-
"""
Astro-Cartography (ACG) Factory (v6.0)

Computes where each planet's angular lines (ASC, DSC, MC, IC) fall
across the globe for a given birth moment. The output is a set of
geographic line coordinates that can be plotted on a map.

Algorithm:
    For a fixed Julian Day, iterate across longitudes (-180 to +180).
    At each longitude, recalculate house cusps using swe.houses_armc()
    and check which planet is closest to each angle (ASC, MC, DSC, IC).
    When a planet's ecliptic longitude matches an angle cusp within
    tolerance, record that longitude as a point on the planet's line.

This is part of Kerykeion (C) 2025 Giacomo Battaglia
"""

import math
import swisseph as swe
from pathlib import Path
from typing import List, Optional, Dict, Literal
from pydantic import BaseModel, Field

from kerykeion.schemas.kr_models import AstrologicalSubjectModel


class ACGLinePoint(BaseModel):
    """A single point on a planetary line."""
    longitude: float = Field(description="Geographic longitude (-180 to +180)")
    latitude: float = Field(description="Geographic latitude (-90 to +90)")


class ACGLine(BaseModel):
    """A planetary line on the astro-cartography map."""
    planet: str = Field(description="Planet name")
    line_type: Literal["ASC", "DSC", "MC", "IC"] = Field(description="Angular line type")
    points: List[ACGLinePoint] = Field(description="Geographic coordinates of the line")


class AstroCartographyFactory:
    """
    Factory for computing astro-cartography (ACG) lines.

    Produces geographic coordinates where each planet's angular lines
    (Ascendant, Descendant, MC, IC) fall across the globe.

    Example:
        >>> subject = AstrologicalSubjectFactory.from_birth_data(...)
        >>> lines = AstroCartographyFactory.compute(subject, step=2)
        >>> for line in lines:
        ...     print(f"{line.planet} {line.line_type}: {len(line.points)} points")
    """

    PLANETS = ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn",
               "Uranus", "Neptune", "Pluto"]

    @staticmethod
    def compute(
        subject: AstrologicalSubjectModel,
        *,
        step: float = 1.0,
        tolerance: Optional[float] = None,
        lat_range: tuple = (-66, 66),
        planets: Optional[List[str]] = None,
    ) -> List[ACGLine]:
        """
        Compute ACG lines for a natal chart.

        Args:
            subject: The natal chart subject.
            step: Longitude/latitude scanning step in degrees (default 1.0).
            tolerance: Angular tolerance for ASC/DSC matching in degrees.
                Defaults to step/2 if not specified. Independent of step.
            lat_range: Latitude range to compute (default -66 to +66, avoids polar).
            planets: List of planet names. Defaults to Sun through Pluto.

        Returns:
            List of ACGLine objects, one per planet per line type.
        """
        if planets is None:
            planets = AstroCartographyFactory.PLANETS

        ephe_path = str(Path(__file__).parent.parent / "sweph")
        swe.set_ephe_path(ephe_path)
        iflag = swe.FLG_SWIEPH | swe.FLG_SPEED

        jd = subject.julian_day

        # Get obliquity and sidereal time
        obliquity = swe.calc_ut(jd, swe.ECL_NUT, iflag)[0][0]
        gst_hours = swe.sidtime(jd)  # Greenwich sidereal time in hours

        # Get planet ecliptic longitudes from the subject
        planet_positions: Dict[str, float] = {}
        for pname in planets:
            point = getattr(subject, pname.lower(), None)
            if point is not None:
                planet_positions[pname] = point.abs_pos

        if not planet_positions:
            swe.close()
            return []

        # Angular tolerance for matching planet to ASC/DSC (independent of scan step)
        match_tol = tolerance if tolerance is not None else step / 2.0

        # MC/IC lines: where the planet crosses the meridian
        # MC longitude = planet_RA - GAST (in degrees)
        # These are vertical lines (constant geographic longitude, all latitudes)
        mc_lines: Dict[str, ACGLine] = {}
        ic_lines: Dict[str, ACGLine] = {}

        for pname, ecl_lon in planet_positions.items():
            # Convert ecliptic longitude to RA
            ecl_rad = math.radians(ecl_lon)
            eps_rad = math.radians(obliquity)
            ra_rad = math.atan2(
                math.sin(ecl_rad) * math.cos(eps_rad),
                math.cos(ecl_rad)
            )
            ra_deg = math.degrees(ra_rad) % 360

            # MC line: geographic longitude where planet is on MC
            mc_geo_lng = (ra_deg - gst_hours * 15.0) % 360
            if mc_geo_lng > 180:
                mc_geo_lng -= 360

            # IC is 180 degrees from MC
            ic_geo_lng = mc_geo_lng + 180 if mc_geo_lng < 0 else mc_geo_lng - 180

            # MC/IC lines are vertical (same lng, range of latitudes)
            lat_min, lat_max = lat_range
            mc_points = [
                ACGLinePoint(longitude=round(mc_geo_lng, 4), latitude=lat)
                for lat in range(int(lat_min), int(lat_max) + 1, max(1, int(step)))
            ]
            ic_points = [
                ACGLinePoint(longitude=round(ic_geo_lng, 4), latitude=lat)
                for lat in range(int(lat_min), int(lat_max) + 1, max(1, int(step)))
            ]

            mc_lines[pname] = ACGLine(planet=pname, line_type="MC", points=mc_points)
            ic_lines[pname] = ACGLine(planet=pname, line_type="IC", points=ic_points)

        # ASC/DSC lines: where the planet rises/sets at each longitude
        # For each longitude, compute ARMC, then find latitude where planet is on ASC
        asc_lines: Dict[str, List[ACGLinePoint]] = {p: [] for p in planet_positions}
        dsc_lines: Dict[str, List[ACGLinePoint]] = {p: [] for p in planet_positions}

        lng = -180.0
        while lng <= 180.0:
            # Local sidereal time -> ARMC
            armc = (gst_hours * 15.0 + lng) % 360

            # For each latitude in range, compute houses and check ASC/DSC
            lat = float(lat_range[0])
            while lat <= lat_range[1]:
                try:
                    cusps, ascmc = swe.houses_armc(armc, lat, obliquity, b"P")
                    asc_deg = ascmc[0]
                    dsc_deg = (asc_deg + 180) % 360

                    for pname, plon in planet_positions.items():
                        # Check ASC proximity
                        asc_diff = abs(plon - asc_deg)
                        if asc_diff > 180:
                            asc_diff = 360 - asc_diff
                        if asc_diff <= match_tol:
                            asc_lines[pname].append(
                                ACGLinePoint(longitude=round(lng, 4), latitude=round(lat, 4))
                            )

                        # Check DSC proximity
                        dsc_diff = abs(plon - dsc_deg)
                        if dsc_diff > 180:
                            dsc_diff = 360 - dsc_diff
                        if dsc_diff <= match_tol:
                            dsc_lines[pname].append(
                                ACGLinePoint(longitude=round(lng, 4), latitude=round(lat, 4))
                            )
                except Exception:
                    pass

                lat += step
            lng += step

        swe.close()

        # Assemble results
        result: List[ACGLine] = []
        for pname in planet_positions:
            result.append(mc_lines[pname])
            result.append(ic_lines[pname])
            if asc_lines[pname]:
                result.append(ACGLine(planet=pname, line_type="ASC", points=asc_lines[pname]))
            if dsc_lines[pname]:
                result.append(ACGLine(planet=pname, line_type="DSC", points=dsc_lines[pname]))

        return result
