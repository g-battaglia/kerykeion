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
from numbers import Real
from kerykeion.ephemeris_backend.backend import ephe, ephemeris_session
from kerykeion.settings.config_constants import POINT_NUMBER_MAP
from typing import List, Optional, Dict, Literal
from pydantic import Field
from kerykeion.schemas.models import SubscriptableBaseModel

from kerykeion.schemas.models import AstrologicalSubjectModel
from kerykeion.schemas import KerykeionException
from kerykeion.utilities.core import wrap_180


class ACGLinePointModel(SubscriptableBaseModel):
    """A single point on a planetary line."""
    longitude: float = Field(description="Geographic longitude (-180 to +180)")
    latitude: float = Field(description="Geographic latitude (-90 to +90)")


class ACGLineModel(SubscriptableBaseModel):
    """A planetary line on the astro-cartography map."""
    planet: str = Field(description="Planet name")
    line_type: Literal["ASC", "DSC", "MC", "IC"] = Field(description="Angular line type")
    points: List[ACGLinePointModel] = Field(description="Geographic coordinates of the line")


# Swiss Ephemeris body ids for the supported ACG planets (shared map).
_ACG_PLANET_IDS: Dict[str, int] = {
    name: POINT_NUMBER_MAP[name]
    for name in ("Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto")
}


def _finite_float(value: object) -> Optional[float]:
    """Coerce a supported real value to float, returning ``None`` if unsafe.

    ``bool`` is rejected: it passes ``Real`` checks (``int`` subclass) but a
    ``True``/``False`` step, latitude, or Julian Day is always a caller mistake.
    """
    if isinstance(value, bool) or not isinstance(value, Real):
        return None
    try:
        converted = float(value)
    except (OverflowError, TypeError, ValueError):
        return None
    return converted if math.isfinite(converted) else None


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
    # Upper bound on the projected number of line points for one compute()
    # call. Generous enough for high-resolution maps (step=0.01 over the full
    # default range with all ten planets stays under it) while still rejecting
    # pathological grids (step=1e-9) that would hang the process.
    MAX_PROJECTED_POINTS = 1_000_000

    @staticmethod
    def compute(
        subject: AstrologicalSubjectModel,
        *,
        step: float = 1.0,
        tolerance: Optional[float] = None,
        lat_range: tuple[float, float] = (-66, 66),
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
                (default 1.0). Must be finite and positive.
            tolerance: Unused since v6 (the horizon equation is solved
                exactly, so there is no proximity matching). Accepted for
                backward compatibility.
            lat_range: Two finite latitude bounds within -90..+90, ordered
                minimum first (default -66 to +66, avoids polar).
            planets: List of supported planet names. Defaults to Sun through
                Pluto. Unknown/malformed entries raise ``KerykeionException``.

        Returns:
            List of ACGLineModel objects, one per planet per line type.

        Raises:
            KerykeionException: For invalid inputs, or when the requested grid
                would project more than ``MAX_PROJECTED_POINTS`` (1,000,000)
                line points — increase ``step``, narrow ``lat_range``, or
                request fewer planets.
        """
        if planets is None:
            requested_planets = list(AstroCartographyFactory.PLANETS)
        else:
            if isinstance(planets, (str, bytes)) or not isinstance(planets, (list, tuple)):
                raise KerykeionException("planets must be a sequence of supported planet names, not a string.")
            invalid_planets = [
                planet
                for planet in planets
                if not isinstance(planet, str) or planet not in _ACG_PLANET_IDS
            ]
            if invalid_planets:
                raise KerykeionException(
                    f"Unknown astro-cartography planets: {invalid_planets!r}. "
                    f"Valid values: {', '.join(AstroCartographyFactory.PLANETS)}."
                )
            requested_planets = list(dict.fromkeys(planets))

        # A non-positive step never advances the latitude scan: the ASC/DSC
        # ``while lat <= lat_max: lat += step`` loop would spin forever. Reject
        # it up front rather than hang.
        step_value = _finite_float(step)
        if step_value is None or step_value <= 0:
            raise KerykeionException(
                f"step must be a finite positive number of degrees, got {step!r}."
            )

        if not isinstance(lat_range, (tuple, list)) or len(lat_range) != 2:
            raise KerykeionException(
                f"lat_range must contain exactly two numeric latitudes, got {lat_range!r}."
            )
        if any(isinstance(value, bool) or not isinstance(value, Real) for value in lat_range):
            raise KerykeionException(
                f"lat_range must contain two finite numeric latitudes, got {lat_range!r}."
            )
        lat_min = _finite_float(lat_range[0])
        lat_max = _finite_float(lat_range[1])
        if lat_min is None or lat_max is None:
            raise KerykeionException(f"lat_range bounds must be finite, got {lat_range!r}.")
        if lat_min < -90 or lat_max > 90:
            raise KerykeionException(
                f"lat_range must stay within -90..90 degrees, got {lat_range!r}."
            )

        # An inverted range (lat_min > lat_max) yields a negative n_steps below
        # and an empty grid — every line would be emitted with no points, no
        # warning. Reject it rather than return silent garbage.
        if lat_min > lat_max:
            raise KerykeionException(
                f"lat_range must be (min, max) with min <= max, got {lat_range!r}."
            )

        subject_jd = subject.julian_day
        # A midpoint composite subject carries julian_day=None (it is a synthetic
        # blend of two charts, not a single instant). Without this guard the None
        # flows into the JD arithmetic below and surfaces as a cryptic
        # "'<' not supported between float and NoneType" from deep inside skyfield.
        if subject_jd is None:
            raise KerykeionException(
                "Subject is missing Julian Day - astro-cartography needs a single birth "
                "instant and cannot be computed for a midpoint composite subject."
            )
        jd = _finite_float(subject_jd)
        if jd is None:
            raise KerykeionException("Subject Julian Day must be finite to compute astro-cartography lines.")

        # Keep only planets that are both supported and present on the
        # subject (mirrors the subject's active points selection). De-duplicate
        # while preserving order: a caller passing the same planet twice must
        # not get duplicate MC/IC lines and doubled ASC/DSC point lists.
        selected: List[str] = []
        _seen: set = set()
        for pname in requested_planets:
            if (
                pname in _ACG_PLANET_IDS
                and pname not in _seen
                and getattr(subject, pname.lower(), None) is not None
            ):
                selected.append(pname)
                _seen.add(pname)
        if not selected:
            return []

        span = lat_max - lat_min
        raw_steps = span / step_value
        projected_points = (raw_steps + 2.0) * len(selected) * 4
        if not math.isfinite(projected_points) or projected_points > AstroCartographyFactory.MAX_PROJECTED_POINTS:
            raise KerykeionException(
                f"Requested ACG grid exceeds the {AstroCartographyFactory.MAX_PROJECTED_POINTS:,}-point "
                "safety limit. "
                "Increase step, narrow lat_range, or request fewer planets."
            )

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

            # One shared float latitude grid for every line type. Previously
            # MC/IC built their grid with range(int(lat_min), ..., max(1, int(step)))
            # — silently coercing a fractional step to an integer (and to >= 1) —
            # while ASC/DSC scanned the true float step, so the two families of
            # lines disagreed on their latitude samples. Build the grid once, in
            # floats, and reuse it everywhere so all lines share the same scan.
            # Integer-indexed grid: accumulating `lat += step` drifts in float
            # (with step=0.1 the last row landed at 65.9 and the requested
            # 66.0 edge was missing from every line).
            n_steps = int(round((lat_max - lat_min) / step_value))
            latitudes: List[float] = [
                round(lat_min + i * step_value, 4)
                for i in range(n_steps + 1)
                if lat_min + i * step_value <= lat_max + 1e-9
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
