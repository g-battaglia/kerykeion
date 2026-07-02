# -*- coding: utf-8 -*-
"""
Astro-Cartography (ACG) Factory (v6.0)

Computes where each planet's angular lines (ASC, DSC, MC, IC) fall
across the globe for a given birth moment. The output is a set of
geographic line coordinates that can be plotted on a map.

Algorithm:
    For a fixed Julian Day, fetch each body's TRUE equatorial
    coordinates (right ascension alpha, declination delta) and the
    Greenwich sidereal time (GST). The body culminates where local
    sidereal time equals alpha, so the MC line is the meridian at
    geographic longitude wrap(alpha - GST) and the IC line is its
    antimeridian. For ASC/DSC, scan geographic latitudes phi and solve
    the horizon equation cos H = -tan(phi) * tan(delta) for the hour
    angle H; rising (H = -H0) and setting (H = +H0) then give the
    geographic longitudes wrap(alpha -/+ H0 - GST) directly.

This is part of Kerykeion (C) 2025 Giacomo Battaglia
"""

import math
from kerykeion.ephemeris_backend import ephe, ephemeris_session
from kerykeion.settings.config_constants import POINT_NUMBER_MAP
from typing import List, Optional, Dict, Literal
from pydantic import BaseModel, Field

from kerykeion.schemas.kr_models import AstrologicalSubjectModel
from kerykeion.schemas import KerykeionException
from kerykeion.utilities import wrap_180


class ACGLinePointModel(BaseModel):
    """A single point on a planetary line."""
    longitude: float = Field(description="Geographic longitude (-180 to +180)")
    latitude: float = Field(description="Geographic latitude (-90 to +90)")


class ACGLineModel(BaseModel):
    """A planetary line on the astro-cartography map."""
    planet: str = Field(description="Planet name")
    line_type: Literal["ASC", "DSC", "MC", "IC"] = Field(description="Angular line type")
    points: List[ACGLinePointModel] = Field(description="Geographic coordinates of the line")


# Swiss Ephemeris body ids for the supported ACG planets (shared map).
_ACG_PLANET_IDS: Dict[str, int] = {
    name: POINT_NUMBER_MAP[name]
    for name in ("Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto")
}


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
    ) -> List[ACGLineModel]:
        """
        Compute ACG lines for a natal chart.

        Lines are computed in mundo, from each body's TRUE equatorial
        coordinates (right ascension and declination): they mark where the
        body physically sits on the local meridian or geometric horizon,
        which does not depend on the zodiac convention. A tropical and a
        sidereal chart of the same instant therefore produce identical
        geographic lines, and bodies with nonzero ecliptic latitude (Moon,
        Pluto, ...) land where reference ACG maps (Jim Lewis / astro.com)
        draw them rather than where their zodiacal degree would project.

        MC/IC lines are the meridians where the body culminates
        (geographic longitude = RA - GST) and anti-culminates. ASC/DSC
        lines solve, per scanned latitude, the horizon equation
        ``cos H = -tan(lat) * tan(declination)``; latitudes where the body
        is circumpolar (or never rises) have no line point. Atmospheric
        refraction is ignored: the lines use the geometric horizon, which
        is also the Jim Lewis convention (refracted rise/set lines would
        sit slightly differently).

        Args:
            subject: The natal chart subject.
            step: Latitude scanning step in degrees for the line points
                (default 1.0).
            tolerance: Unused since v6 (the horizon equation is solved
                exactly, so there is no proximity matching). Accepted for
                backward compatibility.
            lat_range: Latitude range to compute (default -66 to +66, avoids polar).
            planets: List of planet names. Defaults to Sun through Pluto.

        Returns:
            List of ACGLineModel objects, one per planet per line type.
        """
        if planets is None:
            planets = AstroCartographyFactory.PLANETS

        # A non-positive step never advances the latitude scan: the ASC/DSC
        # ``while lat <= lat_max: lat += step`` loop would spin forever. Reject
        # it up front rather than hang.
        if step <= 0:
            raise KerykeionException(
                f"step must be a positive number of degrees, got {step!r}."
            )

        jd = subject.julian_day

        # Keep only planets that are both supported and present on the
        # subject (mirrors the subject's active points selection).
        selected = [
            pname for pname in planets
            if pname in _ACG_PLANET_IDS and getattr(subject, pname.lower(), None) is not None
        ]
        if not selected:
            return []

        mc_lines: Dict[str, ACGLineModel] = {}
        ic_lines: Dict[str, ACGLineModel] = {}
        asc_lines: Dict[str, List[ACGLinePointModel]] = {p: [] for p in selected}
        dsc_lines: Dict[str, List[ACGLinePointModel]] = {p: [] for p in selected}

        with ephemeris_session() as iflag:
            # Greenwich (apparent) sidereal time in degrees; ephe.calc_ut with
            # FLG_EQUATORIAL returns apparent RA/declination of date, so the
            # two are mutually consistent.
            gst_deg = ephe.sidtime(jd) * 15.0

            # Equatorial coordinates are zodiac-independent; drop FLG_SIDEREAL
            # so the fetch is identical for tropical and sidereal charts.
            eq_iflag = (iflag & ~ephe.FLG_SIDEREAL) | ephe.FLG_EQUATORIAL

            lat_min, lat_max = lat_range
            # One shared float latitude grid for every line type. Previously
            # MC/IC built their grid with range(int(lat_min), ..., max(1, int(step)))
            # — silently coercing a fractional step to an integer (and to >= 1) —
            # while ASC/DSC scanned the true float step, so the two families of
            # lines disagreed on their latitude samples. Build the grid once, in
            # floats, and reuse it everywhere so all lines share the same scan.
            # Integer-indexed grid: accumulating `lat += step` drifts in float
            # (with step=0.1 the last row landed at 65.9 and the requested
            # 66.0 edge was missing from every line).
            n_steps = int(round((lat_max - lat_min) / step))
            latitudes: List[float] = [
                round(lat_min + i * step, 4)
                for i in range(n_steps + 1)
                if lat_min + i * step <= lat_max + 1e-9
            ]

            for pname in selected:
                eq_pos = ephe.calc_ut(jd, _ACG_PLANET_IDS[pname], eq_iflag)[0]
                ra_deg, dec_deg = eq_pos[0], eq_pos[1]

                # MC line: the body culminates where LST == RA, i.e. at
                # geographic longitude RA - GST. IC is the antimeridian.
                mc_geo_lng = wrap_180(ra_deg - gst_deg)
                ic_geo_lng = wrap_180(mc_geo_lng + 180.0)

                # MC/IC lines are vertical (same lng, full latitude grid)
                mc_points = [
                    ACGLinePointModel(longitude=round(mc_geo_lng, 4), latitude=lat)
                    for lat in latitudes
                ]
                ic_points = [
                    ACGLinePointModel(longitude=round(ic_geo_lng, 4), latitude=lat)
                    for lat in latitudes
                ]

                mc_lines[pname] = ACGLineModel(planet=pname, line_type="MC", points=mc_points)
                ic_lines[pname] = ACGLineModel(planet=pname, line_type="IC", points=ic_points)

                # ASC/DSC lines: for each latitude, the body is on the
                # geometric horizon when cos H = -tan(lat) * tan(dec). No
                # solution means circumpolar / never rises at that latitude.
                dec_rad = math.radians(dec_deg)
                for lat in latitudes:
                    cos_h0 = -math.tan(math.radians(lat)) * math.tan(dec_rad)
                    if abs(cos_h0) <= 1.0:
                        h0_deg = math.degrees(math.acos(cos_h0))  # in [0, 180]
                        # Rising: hour angle -H0; setting: +H0.
                        rise_lng = wrap_180(ra_deg - h0_deg - gst_deg)
                        set_lng = wrap_180(ra_deg + h0_deg - gst_deg)
                        asc_lines[pname].append(
                            ACGLinePointModel(longitude=round(rise_lng, 4), latitude=lat)
                        )
                        dsc_lines[pname].append(
                            ACGLinePointModel(longitude=round(set_lng, 4), latitude=lat)
                        )

        # Assemble results
        result: List[ACGLineModel] = []
        for pname in selected:
            result.append(mc_lines[pname])
            result.append(ic_lines[pname])
            if asc_lines[pname]:
                result.append(ACGLineModel(planet=pname, line_type="ASC", points=asc_lines[pname]))
            if dsc_lines[pname]:
                result.append(ACGLineModel(planet=pname, line_type="DSC", points=dsc_lines[pname]))

        return result

