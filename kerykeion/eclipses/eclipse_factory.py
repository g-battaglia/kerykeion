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
from typing import List, Optional

from kerykeion.ephemeris_backend import swe, EPHE_DATA_PATH

from kerykeion.schemas.kr_models import SubscriptableBaseModel
from kerykeion.utilities import get_kerykeion_point_from_degree
from pydantic import Field

logger = logging.getLogger(__name__)

_EPHE_PATH = EPHE_DATA_PATH

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


def _zodiac_fields(jd: float, body: int, name: str) -> dict:
    """Ecliptic sign/degree of a luminary at the eclipse maximum.

    Backend-agnostic (uses ``swe.calc_ut``). For a solar eclipse the eclipse
    degree is the Sun/Moon conjunction longitude; for a lunar eclipse it is the
    Moon's longitude (the Full Moon point).
    """
    try:
        lon = float(swe.calc_ut(jd, body, swe.FLG_SWIEPH)[0][0]) % 360.0
        point = get_kerykeion_point_from_degree(lon, name, "AstrologicalPoint")
        return {
            "ecliptic_longitude": round(lon, 6),
            "sign": point.sign,
            "sign_num": point.sign_num,
            "degree": round(point.position, 6),
        }
    except Exception as exc:  # pragma: no cover - defensive
        logger.debug("Eclipse zodiac enrichment failed: %s", exc)
        return {}


def _saros_inex(jd: float, kind: str) -> dict:
    """Saros/Inex series numbers (libephemeris extensions; hasattr-guarded).

    Returns an empty dict on the swisseph backend (functions absent) so the
    extra fields simply stay ``None``.
    """
    out: dict = {}
    saros_fn = getattr(swe, "get_saros_number", None)
    if saros_fn is not None:
        try:
            out["saros"] = int(saros_fn(jd, kind))
        except Exception as exc:  # pragma: no cover - defensive
            logger.debug("Saros lookup failed: %s", exc)
    inex_fn = getattr(swe, "get_inex_number", None)
    if inex_fn is not None:
        try:
            out["inex"] = int(inex_fn(jd, kind))
        except Exception as exc:  # pragma: no cover - defensive
            logger.debug("Inex lookup failed: %s", exc)
    return out


def _solar_gamma_duration(jd: float) -> dict:
    """Solar gamma + central-phase duration (libephemeris extensions; guarded).

    ``sol_eclipse_max_time`` returns ``(jd_max, gamma)`` in global mode (gamma in
    Earth radii); ``calc_solar_eclipse_duration`` returns the totality/annularity
    duration in minutes (0.0 for partial eclipses).
    """
    out: dict = {}
    gamma_fn = getattr(swe, "sol_eclipse_max_time", None)
    if gamma_fn is not None:
        try:
            _, gamma = gamma_fn(jd)
            out["gamma"] = round(float(gamma), 6)
        except Exception as exc:  # pragma: no cover - defensive
            logger.debug("Gamma lookup failed: %s", exc)
    dur_fn = getattr(swe, "calc_solar_eclipse_duration", None)
    if dur_fn is not None:
        try:
            minutes = float(dur_fn(jd))
            out["duration_minutes"] = round(minutes, 4) if minutes > 0 else None
        except Exception as exc:  # pragma: no cover - defensive
            logger.debug("Duration lookup failed: %s", exc)
    return out


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
    # Zodiac position of the eclipse (Sun/Moon conjunction longitude at maximum).
    ecliptic_longitude: Optional[float] = Field(default=None, description="Ecliptic longitude at maximum (0-360)")
    sign: Optional[str] = Field(default=None, description="Zodiac sign of the eclipse")
    sign_num: Optional[int] = Field(default=None, description="Zodiac sign number (0=Aries)")
    degree: Optional[float] = Field(default=None, description="Degree within the sign (0-30)")
    # Catalogued series + geometry (libephemeris extensions; None on swisseph backend).
    saros: Optional[int] = Field(default=None, description="Saros series number")
    inex: Optional[int] = Field(default=None, description="Inex series number")
    gamma: Optional[float] = Field(default=None, description="Gamma: shadow-axis distance from Earth's centre (Earth radii)")
    duration_minutes: Optional[float] = Field(default=None, description="Central (total/annular) duration in minutes; None if partial")


class LunarEclipseModel(SubscriptableBaseModel):
    """Lunar eclipse data."""
    type: str = Field(description="Eclipse type: total, partial, penumbral")
    maximum_jd: float = Field(description="Julian Day of maximum eclipse")
    datestamp: str = Field(description="ISO 8601 formatted datetime of maximum")
    magnitude_umbral: Optional[float] = Field(default=None, description="Umbral magnitude")
    magnitude_penumbral: Optional[float] = Field(default=None, description="Penumbral magnitude")
    # Zodiac position of the eclipse (Moon longitude / Full Moon point at maximum).
    ecliptic_longitude: Optional[float] = Field(default=None, description="Ecliptic longitude at maximum (0-360)")
    sign: Optional[str] = Field(default=None, description="Zodiac sign of the eclipse")
    sign_num: Optional[int] = Field(default=None, description="Zodiac sign number (0=Aries)")
    degree: Optional[float] = Field(default=None, description="Degree within the sign (0-30)")
    # Catalogued series (libephemeris extensions; None on swisseph backend).
    saros: Optional[int] = Field(default=None, description="Saros series number")
    inex: Optional[int] = Field(default=None, description="Inex series number")


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
    """Find upcoming solar and lunar eclipses visible globally or from a specific location.

    Provides two search modes:
    - ``search_from_location()``: finds eclipses visible from given coordinates.
    - ``search_global()``: finds eclipses regardless of observer position.

    Example:
        >>> from kerykeion import EclipseFactory
        >>> results = EclipseFactory.search_from_location(lat=41.90, lng=12.49)
    """

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
        """Search for solar eclipses visible from a geographic position."""
        results = []
        jd = start_jd
        for _ in range(count):
            try:
                retflags, tret, attr = swe.sol_eclipse_when_loc(jd, geopos, swe.FLG_SWIEPH)
                if tret[0] == 0.0:
                    break
                max_jd = tret[0]
                results.append(SolarEclipseModel(
                    type=_classify_solar_eclipse(retflags),
                    maximum_jd=max_jd,
                    datestamp=_jd_to_iso(max_jd),
                    magnitude=round(attr[0], 6) if len(attr) > 0 else 0.0,
                    obscuration=round(attr[2], 6) if len(attr) > 2 else 0.0,
                    sun_altitude=round(attr[5], 4) if len(attr) > 5 else None,
                    **_zodiac_fields(max_jd, swe.SUN, "Sun"),
                    **_saros_inex(max_jd, "solar"),
                    **_solar_gamma_duration(max_jd),
                ))
                jd = max_jd + 10  # Skip ahead
            except Exception as e:
                logger.warning(f"Solar eclipse search error: {e}")
                break
        return results

    @staticmethod
    def _find_solar_global(start_jd: float, count: int) -> List[SolarEclipseModel]:
        """Search for solar eclipses globally (any location on Earth)."""
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
                    **_zodiac_fields(max_jd, swe.SUN, "Sun"),
                    **_saros_inex(max_jd, "solar"),
                    **_solar_gamma_duration(max_jd),
                ))
                jd = max_jd + 10
            except Exception as e:
                logger.warning(f"Global solar eclipse search error: {e}")
                break
        return results

    @staticmethod
    def _find_lunar_local(start_jd: float, geopos: tuple, count: int) -> List[LunarEclipseModel]:
        """Search for lunar eclipses visible from a geographic position."""
        results = []
        jd = start_jd
        for _ in range(count):
            try:
                retflags, tret, attr = swe.lun_eclipse_when_loc(jd, geopos, swe.FLG_SWIEPH)
                if tret[0] == 0.0:
                    break
                max_jd = tret[0]
                results.append(LunarEclipseModel(
                    type=_classify_lunar_eclipse(retflags),
                    maximum_jd=max_jd,
                    datestamp=_jd_to_iso(max_jd),
                    magnitude_umbral=round(attr[0], 6) if len(attr) > 0 else None,
                    magnitude_penumbral=round(attr[1], 6) if len(attr) > 1 else None,
                    **_zodiac_fields(max_jd, swe.MOON, "Moon"),
                    **_saros_inex(max_jd, "lunar"),
                ))
                jd = max_jd + 10
            except Exception as e:
                logger.warning(f"Lunar eclipse search error: {e}")
                break
        return results

    @staticmethod
    def _find_lunar_global(start_jd: float, count: int) -> List[LunarEclipseModel]:
        """Search for lunar eclipses globally."""
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
                    **_zodiac_fields(max_jd, swe.MOON, "Moon"),
                    **_saros_inex(max_jd, "lunar"),
                ))
                jd = max_jd + 10
            except Exception as e:
                logger.warning(f"Global lunar eclipse search error: {e}")
                break
        return results
