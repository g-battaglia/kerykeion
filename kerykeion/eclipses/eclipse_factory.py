# -*- coding: utf-8 -*-
"""Find upcoming solar and lunar eclipses, optionally for a specific location.

Swiss Ephemeris functions used:
    - ephe.sol_eclipse_when_loc(tjdut, geopos, flags, backwards)
    - ephe.sol_eclipse_when_glob(tjdut, flags, ecl_type, backwards)
    - ephe.lun_eclipse_when(tjdut, flags, ecl_type, backwards)
    - ephe.lun_eclipse_when_loc(tjdut, geopos, flags, backwards)

Eclipse type bit flags (pyswisseph uses both SE_ prefix and non-prefix):
    ECL_TOTAL, ECL_ANNULAR, ECL_PARTIAL, ECL_PENUMBRAL
"""

from __future__ import annotations

import logging
from typing import List, Optional

from kerykeion.ephemeris_backend import ephe, ephemeris_session
from kerykeion._predictive_utils import jd_to_iso_utc as _jd_to_iso

from kerykeion.schemas.kerykeion_exception import KerykeionException
from kerykeion.schemas.kr_literals import AstrologicalPoint
from kerykeion.schemas.kr_models import SubscriptableBaseModel
from kerykeion.utilities import get_kerykeion_point_from_degree
from pydantic import Field

logger = logging.getLogger(__name__)

# Backstop on events per type per search. Each event is found with a single
# backend call, so this still allows centuries of coverage; absurd requests are
# rejected upfront (like the range factories' ``_ensure_scannable``) rather
# than left to fail mid-scan or silently truncate.
_MAX_COUNT = 1_000

# Eclipse type constants (handle SE_ prefix variance across pyswisseph builds)
ECL_TOTAL = getattr(ephe, "SE_ECL_TOTAL", getattr(ephe, "ECL_TOTAL", 4))
ECL_ANNULAR = getattr(ephe, "SE_ECL_ANNULAR", getattr(ephe, "ECL_ANNULAR", 8))
ECL_PARTIAL = getattr(ephe, "SE_ECL_PARTIAL", getattr(ephe, "ECL_PARTIAL", 16))
ECL_PENUMBRAL = getattr(ephe, "SE_ECL_PENUMBRAL", getattr(ephe, "ECL_PENUMBRAL", 64))
ECL_ANNULAR_TOTAL = getattr(ephe, "SE_ECL_ANNULAR_TOTAL", getattr(ephe, "ECL_ANNULAR_TOTAL", 32))



def _ensure_scannable(count: int) -> None:
    """Reject absurd event counts upfront, so a caller never receives a
    silently truncated result and never waits on a scan that cannot finish."""
    if count > _MAX_COUNT:
        raise ValueError(
            f"count too large (> {_MAX_COUNT} events per eclipse type). "
            f"Request fewer events per search."
        )


def _search_failure(kind: str, jd: float, exc: Exception) -> KerykeionException:
    """Build the exception raised when the backend fails mid-scan.

    A failing eclipse primitive call must abort the search: logging and
    returning the events found so far would silently truncate a result that
    still claims full coverage. The most common cause is a search that walked
    past the edge of the available ephemeris data.
    """
    return KerykeionException(
        f"{kind} eclipse search failed at JD {jd:.5f}: {exc}. "
        f"This usually means the search reached a date outside the available "
        f"ephemeris range; use a start_year/count combination covered by the "
        f"installed ephemeris data."
    )


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


def _zodiac_fields(jd: float, body: int, name: AstrologicalPoint) -> dict:
    """Ecliptic sign/degree of a luminary at the eclipse maximum.

    Backend-agnostic (uses ``ephe.calc_ut``). For a solar eclipse the eclipse
    degree is the Sun/Moon conjunction longitude; for a lunar eclipse it is the
    Moon's longitude (the Full Moon point).
    """
    try:
        lon = float(ephe.calc_ut(jd, body, ephe.FLG_SWIEPH)[0][0]) % 360.0
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
    """Saros series number (libephemeris extension; hasattr-guarded).

    Returns an empty dict on the swisseph backend (function absent) so the
    extra fields simply stay ``None``. libephemeris returns 0 when the eclipse
    is missing from its catalog tables; a non-positive number is therefore
    "not catalogued", never a real series, and must not be forwarded as a
    plausible-looking value.

    The ``inex`` field is deliberately NOT populated: libephemeris (<= 2.0.2)
    ``get_inex_number`` matches the nearest of a handful of reference eclipses
    with no residual threshold (unlike its saros twin), so it returns a
    plausible-looking constant for arbitrary eclipses instead of failing —
    verified: every eclipse in 2026-2027 reports inex 50 with residuals of
    hundreds of days. Until upstream applies a residual cutoff, None is the
    only honest value.
    """
    out: dict = {}
    saros_fn = getattr(ephe, "get_saros_number", None)
    if saros_fn is not None:
        try:
            saros = int(saros_fn(jd, kind))
            if saros > 0:
                out["saros"] = saros
        except Exception as exc:  # pragma: no cover - defensive
            logger.debug("Saros lookup failed: %s", exc)
    return out


def _solar_gamma_duration(jd: float) -> dict:
    """Solar gamma + central-phase duration (libephemeris extensions; guarded).

    ``sol_eclipse_max_time`` returns ``(jd_max, gamma)`` in global mode (gamma in
    Earth radii); ``calc_solar_eclipse_duration`` returns the duration of the
    central (total/annular) phase across the Earth's surface in minutes -- the
    global span of the central shadow path from first to last contact with
    Earth, NOT the totality duration at any single place (which is only a few
    minutes). 0.0 for partial eclipses.
    """
    out: dict = {}
    gamma_fn = getattr(ephe, "sol_eclipse_max_time", None)
    if gamma_fn is not None:
        try:
            _, gamma = gamma_fn(jd)
            out["gamma"] = round(float(gamma), 6)
        except Exception as exc:  # pragma: no cover - defensive
            logger.debug("Gamma lookup failed: %s", exc)
    dur_fn = getattr(ephe, "calc_solar_eclipse_duration", None)
    if dur_fn is not None:
        try:
            minutes = float(dur_fn(jd))
            out["duration_minutes"] = round(minutes, 4) if minutes > 0 else None
        except Exception as exc:  # pragma: no cover - defensive
            logger.debug("Duration lookup failed: %s", exc)
    return out


def _lunar_magnitudes(jd: float) -> dict:
    """Umbral/penumbral magnitudes at a lunar eclipse maximum (guarded).

    Unlike solar magnitude/obscuration, lunar eclipse magnitudes are
    observer-independent (the Moon either is or is not inside Earth's shadow),
    so a global search can report them too. ``ephe.lun_eclipse_how`` (standard
    on both backends) is evaluated at the global maximum; the geographic
    position only affects the local-visibility attributes, not the magnitudes
    in ``attr[0]``/``attr[1]``, so a dummy geopos is sufficient.
    """
    out: dict = {}
    how_fn = getattr(ephe, "lun_eclipse_how", None)
    if how_fn is None:  # pragma: no cover - both backends expose it
        return out
    try:
        _, attr = how_fn(jd, (0.0, 0.0, 0.0), ephe.FLG_SWIEPH)
        if len(attr) > 0:
            out["magnitude_umbral"] = round(float(attr[0]), 6)
        if len(attr) > 1:
            out["magnitude_penumbral"] = round(float(attr[1]), 6)
    except Exception as exc:  # pragma: no cover - defensive
        logger.debug("Lunar magnitude lookup failed: %s", exc)
    return out


# =============================================================================
# MODELS
# =============================================================================


class SolarEclipseModel(SubscriptableBaseModel):
    """Solar eclipse data."""
    type: str = Field(description="Eclipse type: total, annular, partial, annular-total")
    maximum_jd: float = Field(description="Julian Day of maximum eclipse")
    datestamp: str = Field(description="ISO 8601 formatted datetime of maximum")
    magnitude: Optional[float] = Field(default=None, description="Fraction of solar diameter covered; None for global searches, populated for local searches")
    obscuration: Optional[float] = Field(default=None, description="Fraction of solar disk area covered; None for global searches, populated for local searches")
    sun_altitude: Optional[float] = Field(default=None, description="Sun altitude at maximum (degrees)")
    # Zodiac position of the eclipse (Sun/Moon conjunction longitude at maximum).
    ecliptic_longitude: Optional[float] = Field(default=None, description="Ecliptic longitude at maximum (0-360)")
    sign: Optional[str] = Field(default=None, description="Zodiac sign of the eclipse")
    sign_num: Optional[int] = Field(default=None, description="Zodiac sign number (0=Aries)")
    degree: Optional[float] = Field(default=None, description="Degree within the sign (0-30)")
    # Catalogued series + geometry (libephemeris extensions; None on swisseph backend).
    saros: Optional[int] = Field(default=None, description="Saros series number (None on the swisseph backend or when the eclipse is absent from the catalog tables)")
    inex: Optional[int] = Field(default=None, description="Inex series number. Currently always None: libephemeris <= 2.0.2 get_inex_number lacks a residual threshold and returns nearest-series values for arbitrary eclipses; the field is reserved until a trustworthy source is available")
    gamma: Optional[float] = Field(default=None, description="Gamma: shadow-axis distance from Earth's centre (Earth radii)")
    duration_minutes: Optional[float] = Field(default=None, description="Duration of the central (total/annular) phase across the Earth's surface in minutes (global central-path span, not the local totality duration at one place); None if partial")


class LunarEclipseModel(SubscriptableBaseModel):
    """Lunar eclipse data."""
    type: str = Field(description="Eclipse type: total, partial, penumbral")
    maximum_jd: float = Field(description="Julian Day of maximum eclipse")
    datestamp: str = Field(description="ISO 8601 formatted datetime of maximum")
    magnitude_umbral: Optional[float] = Field(default=None, description="Umbral magnitude at maximum_jd, populated in both global and local searches (lunar magnitudes are observer-independent; non-positive when the Moon misses the umbra, i.e. penumbral eclipses)")
    magnitude_penumbral: Optional[float] = Field(default=None, description="Penumbral magnitude at maximum_jd, populated in both global and local searches (lunar magnitudes are observer-independent)")
    # Zodiac position of the eclipse (Moon longitude / Full Moon point at maximum).
    ecliptic_longitude: Optional[float] = Field(default=None, description="Ecliptic longitude at maximum (0-360)")
    sign: Optional[str] = Field(default=None, description="Zodiac sign of the eclipse")
    sign_num: Optional[int] = Field(default=None, description="Zodiac sign number (0=Aries)")
    degree: Optional[float] = Field(default=None, description="Degree within the sign (0-30)")
    # Catalogued series (libephemeris extensions; None on swisseph backend).
    saros: Optional[int] = Field(default=None, description="Saros series number (None on the swisseph backend or when the eclipse is absent from the catalog tables)")
    inex: Optional[int] = Field(default=None, description="Inex series number. Currently always None: libephemeris <= 2.0.2 get_inex_number lacks a residual threshold and returns nearest-series values for arbitrary eclipses; the field is reserved until a trustworthy source is available")


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

        Raises:
            KerykeionException: If the ephemeris backend fails mid-search (most
                often a date outside the available ephemeris range); the search
                never returns silently truncated results.
            ValueError: If ``count`` exceeds the supported maximum.
        """
        _ensure_scannable(count)
        geopos = (lng, lat, 0.0)
        start_jd = ephe.julday(start_year, 1, 1, 0.0)

        # The session holds the ephemeris lock across the whole scan (the
        # eclipse primitives read process-global backend state shared with
        # chart calculations) and resets that state on exit without degrading
        # the backend.
        with ephemeris_session():
            solar_eclipses = EclipseFactory._find_solar_local(start_jd, geopos, count)
            lunar_eclipses = EclipseFactory._find_lunar_local(start_jd, geopos, count)

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
            EclipseSearchResultModel with solar and lunar eclipses. Global
            solar results carry ``magnitude``/``obscuration`` as ``None`` (they
            are observer-dependent quantities; use a local search to obtain
            them). Lunar magnitudes are observer-independent and are populated
            in global results too.

        Raises:
            KerykeionException: If the ephemeris backend fails mid-search (most
                often a date outside the available ephemeris range); the search
                never returns silently truncated results.
            ValueError: If ``count`` exceeds the supported maximum.
        """
        _ensure_scannable(count)
        start_jd = ephe.julday(start_year, 1, 1, 0.0)

        with ephemeris_session():
            solar_eclipses = EclipseFactory._find_solar_global(start_jd, count)
            lunar_eclipses = EclipseFactory._find_lunar_global(start_jd, count)

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
                retflags, tret, attr = ephe.sol_eclipse_when_loc(jd, geopos, ephe.FLG_SWIEPH)
            except Exception as exc:
                raise _search_failure("Local solar", jd, exc) from exc
            if tret[0] == 0.0:
                # Defensive: both backends raise instead of returning a zero JD
                # when no further eclipse exists; kept as a belt-and-braces
                # guard against a pathological zero result.
                break
            max_jd = tret[0]
            results.append(SolarEclipseModel(
                type=_classify_solar_eclipse(retflags),
                maximum_jd=max_jd,
                datestamp=_jd_to_iso(max_jd),
                magnitude=round(attr[0], 6) if len(attr) > 0 else None,
                obscuration=round(attr[2], 6) if len(attr) > 2 else None,
                sun_altitude=round(attr[5], 4) if len(attr) > 5 else None,
                **_zodiac_fields(max_jd, ephe.SUN, "Sun"),
                **_saros_inex(max_jd, "solar"),
                # gamma / duration are global central-line properties; max_jd
                # here is the observer's local maximum, so they are omitted
                # (the global search reports them from the global maximum).
            ))
            jd = max_jd + 10  # Skip ahead
        return results

    @staticmethod
    def _find_solar_global(start_jd: float, count: int) -> List[SolarEclipseModel]:
        """Search for solar eclipses globally (any location on Earth)."""
        results = []
        jd = start_jd
        for _ in range(count):
            try:
                retflags, tret = ephe.sol_eclipse_when_glob(jd, ephe.FLG_SWIEPH)
            except Exception as exc:
                raise _search_failure("Global solar", jd, exc) from exc
            if tret[0] == 0.0:
                # Defensive: both backends raise instead of returning a zero JD
                # when no further eclipse exists; kept as a belt-and-braces
                # guard against a pathological zero result.
                break
            max_jd = tret[0]
            results.append(SolarEclipseModel(
                type=_classify_solar_eclipse(retflags),
                maximum_jd=max_jd,
                datestamp=_jd_to_iso(max_jd),
                # magnitude/obscuration are observer-dependent: None in global mode.
                magnitude=None,
                obscuration=None,
                **_zodiac_fields(max_jd, ephe.SUN, "Sun"),
                **_saros_inex(max_jd, "solar"),
                **_solar_gamma_duration(max_jd),
            ))
            jd = max_jd + 10
        return results

    @staticmethod
    def _find_lunar_local(start_jd: float, geopos: tuple, count: int) -> List[LunarEclipseModel]:
        """Search for lunar eclipses visible from a geographic position."""
        results = []
        jd = start_jd
        for _ in range(count):
            try:
                retflags, tret, attr = ephe.lun_eclipse_when_loc(jd, geopos, ephe.FLG_SWIEPH)
            except Exception as exc:
                raise _search_failure("Local lunar", jd, exc) from exc
            if tret[0] == 0.0:
                # Defensive: both backends raise instead of returning a zero JD
                # when no further eclipse exists; kept as a belt-and-braces
                # guard against a pathological zero result.
                break
            max_jd = tret[0]
            results.append(LunarEclipseModel(
                type=_classify_lunar_eclipse(retflags),
                maximum_jd=max_jd,
                datestamp=_jd_to_iso(max_jd),
                magnitude_umbral=round(attr[0], 6) if len(attr) > 0 else None,
                magnitude_penumbral=round(attr[1], 6) if len(attr) > 1 else None,
                **_zodiac_fields(max_jd, ephe.MOON, "Moon"),
                **_saros_inex(max_jd, "lunar"),
            ))
            jd = max_jd + 10
        return results

    @staticmethod
    def _find_lunar_global(start_jd: float, count: int) -> List[LunarEclipseModel]:
        """Search for lunar eclipses globally."""
        results = []
        jd = start_jd
        for _ in range(count):
            try:
                retflags, tret = ephe.lun_eclipse_when(jd, ephe.FLG_SWIEPH, 0)
            except Exception as exc:
                raise _search_failure("Global lunar", jd, exc) from exc
            if tret[0] == 0.0:
                # Defensive: both backends raise instead of returning a zero JD
                # when no further eclipse exists; kept as a belt-and-braces
                # guard against a pathological zero result.
                break
            max_jd = tret[0]
            results.append(LunarEclipseModel(
                type=_classify_lunar_eclipse(retflags),
                maximum_jd=max_jd,
                datestamp=_jd_to_iso(max_jd),
                # Lunar magnitudes are observer-independent, so (unlike the
                # solar fields) they are populated in global mode too.
                **_lunar_magnitudes(max_jd),
                **_zodiac_fields(max_jd, ephe.MOON, "Moon"),
                **_saros_inex(max_jd, "lunar"),
            ))
            jd = max_jd + 10
        return results
