# -*- coding: utf-8 -*-
"""Find upcoming solar and lunar eclipses, optionally for a specific location.

Swiss Ephemeris functions used:
    - swe.sol_eclipse_when_loc(tjdut, geopos, flags, backwards)
    - swe.sol_eclipse_when_glob(tjdut, flags, ecl_type, backwards)
    - swe.lun_eclipse_when(tjdut, flags, ecl_type, backwards)
    - swe.lun_eclipse_when_loc(tjdut, geopos, flags, backwards)

Eclipse type bit flags (pyswisseph uses both SE_ prefix and non-prefix):
    ECL_TOTAL, ECL_ANNULAR, ECL_PARTIAL, ECL_PENUMBRAL
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

import swisseph as swe

from kerykeion.schemas.kr_models import SubscriptableBaseModel
from pydantic import Field

_EPHE_PATH = str(Path(__file__).parent.parent / "sweph")

# Eclipse type constants (handle SE_ prefix variance across pyswisseph builds)
ECL_TOTAL = getattr(swe, "SE_ECL_TOTAL", getattr(swe, "ECL_TOTAL", 4))
ECL_ANNULAR = getattr(swe, "SE_ECL_ANNULAR", getattr(swe, "ECL_ANNULAR", 8))
ECL_PARTIAL = getattr(swe, "SE_ECL_PARTIAL", getattr(swe, "ECL_PARTIAL", 16))
ECL_PENUMBRAL = getattr(swe, "SE_ECL_PENUMBRAL", getattr(swe, "ECL_PENUMBRAL", 64))
ECL_ANNULAR_TOTAL = getattr(swe, "SE_ECL_ANNULAR_TOTAL", getattr(swe, "ECL_ANNULAR_TOTAL", 32))


def _jd_to_iso(jd: float) -> str:
    """Convert Julian Day to ISO 8601 string."""
    try:
        year, month, day, hour_frac = swe.revjul(jd)
        hours = int(hour_frac)
        minutes = int((hour_frac - hours) * 60)
        return f"{year:04d}-{month:02d}-{day:02d}T{hours:02d}:{minutes:02d}:00Z"
    except Exception:
        return ""


def _classify_solar_eclipse(retflags: int) -> str:
    """Classify solar eclipse type from return flags."""
    if retflags & ECL_TOTAL:
        return "total"
    elif retflags & ECL_ANNULAR_TOTAL:
        return "annular-total"
    elif retflags & ECL_ANNULAR:
        return "annular"
    elif retflags & ECL_PARTIAL:
        return "partial"
    return "unknown"


def _classify_lunar_eclipse(retflags: int) -> str:
    """Classify lunar eclipse type from return flags."""
    if retflags & ECL_TOTAL:
        return "total"
    elif retflags & ECL_PARTIAL:
        return "partial"
    elif retflags & ECL_PENUMBRAL:
        return "penumbral"
    return "unknown"


# =============================================================================
# MODELS
# =============================================================================


class SolarEclipseModel(SubscriptableBaseModel):
    """Solar eclipse data."""
    type: str = Field(description="Eclipse type: total, annular, partial, annular-total")
    maximum_jd: float = Field(description="Julian Day of maximum eclipse")
    datestamp: str = Field(description="ISO 8601 formatted datetime of maximum")
    magnitude: float = Field(description="Fraction of solar diameter covered")
    obscuration: float = Field(description="Fraction of solar disk area covered")
    sun_altitude: Optional[float] = Field(default=None, description="Sun altitude at maximum (degrees)")


class LunarEclipseModel(SubscriptableBaseModel):
    """Lunar eclipse data."""
    type: str = Field(description="Eclipse type: total, partial, penumbral")
    maximum_jd: float = Field(description="Julian Day of maximum eclipse")
    datestamp: str = Field(description="ISO 8601 formatted datetime of maximum")
    magnitude_umbral: Optional[float] = Field(default=None, description="Umbral magnitude")
    magnitude_penumbral: Optional[float] = Field(default=None, description="Penumbral magnitude")


class EclipseSearchResultModel(SubscriptableBaseModel):
    """Result of an eclipse search."""
    solar_eclipses: List[SolarEclipseModel] = Field(description="Solar eclipses found")
    lunar_eclipses: List[LunarEclipseModel] = Field(description="Lunar eclipses found")
    latitude: Optional[float] = Field(default=None, description="Search latitude (None for global)")
    longitude: Optional[float] = Field(default=None, description="Search longitude (None for global)")


# =============================================================================
# FACTORY
# =============================================================================


class EclipseFactory:
    """Find upcoming solar and lunar eclipses."""

    @staticmethod
    def search_from_location(
        lat: float,
        lng: float,
        start_year: int = 2025,
        count: int = 5,
    ) -> EclipseSearchResultModel:
        """Search for eclipses visible from a specific location.

        Args:
            lat: Geographic latitude (north positive).
            lng: Geographic longitude (east positive).
            start_year: Year to start searching from.
            count: Number of each type to find.

        Returns:
            EclipseSearchResultModel with solar and lunar eclipses.
        """
        swe.set_ephe_path(_EPHE_PATH)
        geopos = (lng, lat, 0.0)
        start_jd = swe.julday(start_year, 1, 1, 0.0)

        solar_eclipses = EclipseFactory._find_solar_local(start_jd, geopos, count)
        lunar_eclipses = EclipseFactory._find_lunar_local(start_jd, geopos, count)

        swe.close()
        return EclipseSearchResultModel(
            solar_eclipses=solar_eclipses,
            lunar_eclipses=lunar_eclipses,
            latitude=lat,
            longitude=lng,
        )

    @staticmethod
    def search_global(
        start_year: int = 2025,
        count: int = 10,
    ) -> EclipseSearchResultModel:
        """Search for global eclipses (any location).

        Args:
            start_year: Year to start searching from.
            count: Number of each type to find.

        Returns:
            EclipseSearchResultModel with solar and lunar eclipses.
        """
        swe.set_ephe_path(_EPHE_PATH)
        start_jd = swe.julday(start_year, 1, 1, 0.0)

        solar_eclipses = EclipseFactory._find_solar_global(start_jd, count)
        lunar_eclipses = EclipseFactory._find_lunar_global(start_jd, count)

        swe.close()
        return EclipseSearchResultModel(
            solar_eclipses=solar_eclipses,
            lunar_eclipses=lunar_eclipses,
        )

    @staticmethod
    def _find_solar_local(start_jd: float, geopos: tuple, count: int) -> List[SolarEclipseModel]:
        results = []
        jd = start_jd
        for _ in range(count):
            try:
                retflags, tret, attr = swe.sol_eclipse_when_loc(jd, geopos)
                if tret[0] == 0.0:
                    break
                max_jd = tret[0]
                results.append(SolarEclipseModel(
                    type=_classify_solar_eclipse(retflags),
                    maximum_jd=max_jd,
                    datestamp=_jd_to_iso(max_jd),
                    magnitude=round(attr[1], 6) if len(attr) > 1 else 0.0,
                    obscuration=round(attr[2], 6) if len(attr) > 2 else 0.0,
                    sun_altitude=round(attr[3], 4) if len(attr) > 3 else None,
                ))
                jd = max_jd + 10  # Skip ahead
            except Exception as e:
                logging.warning(f"Solar eclipse search error: {e}")
                break
        return results

    @staticmethod
    def _find_solar_global(start_jd: float, count: int) -> List[SolarEclipseModel]:
        results = []
        jd = start_jd
        for _ in range(count):
            try:
                retflags, tret = swe.sol_eclipse_when_glob(jd, swe.FLG_SWIEPH)
                if tret[0] == 0.0:
                    break
                max_jd = tret[0]
                results.append(SolarEclipseModel(
                    type=_classify_solar_eclipse(retflags),
                    maximum_jd=max_jd,
                    datestamp=_jd_to_iso(max_jd),
                    magnitude=0.0,
                    obscuration=0.0,
                ))
                jd = max_jd + 10
            except Exception as e:
                logging.warning(f"Global solar eclipse search error: {e}")
                break
        return results

    @staticmethod
    def _find_lunar_local(start_jd: float, geopos: tuple, count: int) -> List[LunarEclipseModel]:
        results = []
        jd = start_jd
        for _ in range(count):
            try:
                retflags, tret, attr = swe.lun_eclipse_when_loc(jd, geopos)
                if tret[0] == 0.0:
                    break
                max_jd = tret[0]
                results.append(LunarEclipseModel(
                    type=_classify_lunar_eclipse(retflags),
                    maximum_jd=max_jd,
                    datestamp=_jd_to_iso(max_jd),
                    magnitude_umbral=round(attr[0], 6) if len(attr) > 0 else None,
                    magnitude_penumbral=round(attr[1], 6) if len(attr) > 1 else None,
                ))
                jd = max_jd + 10
            except Exception as e:
                logging.warning(f"Lunar eclipse search error: {e}")
                break
        return results

    @staticmethod
    def _find_lunar_global(start_jd: float, count: int) -> List[LunarEclipseModel]:
        results = []
        jd = start_jd
        for _ in range(count):
            try:
                retflags, tret = swe.lun_eclipse_when(jd, swe.FLG_SWIEPH, 0)
                if tret[0] == 0.0:
                    break
                max_jd = tret[0]
                results.append(LunarEclipseModel(
                    type=_classify_lunar_eclipse(retflags),
                    maximum_jd=max_jd,
                    datestamp=_jd_to_iso(max_jd),
                ))
                jd = max_jd + 10
            except Exception as e:
                logging.warning(f"Global lunar eclipse search error: {e}")
                break
        return results
