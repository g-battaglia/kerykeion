# -*- coding: utf-8 -*-
"""
Pure domain helpers for the dominants calculator.
==================================================

These functions are deliberately free of any Pydantic model construction and of
any I/O beyond the (locked) ephemeris call needed for the prenatal syzygy. They
turn a computed :class:`AstrologicalSubjectModel` into the small primitives the
strategies need — angle degrees, house cusps, the list of scoring planets, a
zodiacal breakdown of an arbitrary degree, rulership lookups and the prenatal
syzygy — so each scoring school can stay focused on *weighting*, not plumbing.

This is part of Kerykeion (C) 2025 Giacomo Battaglia
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional

from kerykeion.dominants.data import (
    MODERN_RULERS,
    SIGN_NUM_TO_ELEMENT,
    SIGN_NUM_TO_QUALITY,
)
from kerykeion.ephemeris_backend import EPHEMERIS_LOCK, swe
from kerykeion.moon_phase_details.utils import configure_ephemeris_path
from kerykeion.schemas.kr_literals import SIGN_CODES, Element, Quality, Sign
from kerykeion.schemas.kr_models import AstrologicalSubjectModel, KerykeionPointModel

logger = logging.getLogger(__name__)

# =============================================================================
# SMALL VALUE OBJECTS
# =============================================================================

#: Internal attribute names of the ten traditional + modern planets on a subject,
#: in canonical order. ``point.name`` exposes the public Title-case name.
_PLANET_ATTRS: tuple[str, ...] = (
    "sun",
    "moon",
    "mercury",
    "venus",
    "mars",
    "jupiter",
    "saturn",
    "uranus",
    "neptune",
    "pluto",
)

#: The four chart angles, public name -> subject attribute.
_ANGLE_ATTRS: Dict[str, str] = {
    "Ascendant": "ascendant",
    "Medium_Coeli": "medium_coeli",
    "Descendant": "descendant",
    "Imum_Coeli": "imum_coeli",
}

#: Subject attributes holding the twelve house cusps, in order 1..12.
_HOUSE_ATTRS: tuple[str, ...] = (
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
)


@dataclass(frozen=True)
class ZodiacPosition:
    """The zodiacal breakdown of an absolute ecliptic longitude.

    Attributes:
        sign: Three-letter sign code (e.g. "Ari").
        sign_num: Sign index 0-11 (Aries = 0).
        position: Degree within the sign (0-30).
        element: Title-case element of the sign.
        quality: Title-case modality of the sign.
    """

    sign: Sign
    sign_num: int
    position: float
    element: Element
    quality: Quality


@dataclass(frozen=True)
class SyzygyInfo:
    """The prenatal syzygy (the New or Full Moon immediately before birth).

    Attributes:
        degree: Absolute ecliptic longitude of the syzygy, already expressed in
            the subject's zodiac (tropical or sidereal).
        kind: "New" for a preceding New Moon, "Full" for a preceding Full Moon.
        julian_day: Julian Day (UT) of the syzygy.
    """

    degree: float
    kind: str
    julian_day: float


# =============================================================================
# ZODIAC / GEOMETRY HELPERS
# =============================================================================


def zodiac_breakdown(degree: float) -> ZodiacPosition:
    """Break an absolute ecliptic longitude into sign, degree, element, modality.

    Args:
        degree: Absolute longitude in degrees (any real number; normalized to
            ``[0, 360)``).

    Returns:
        The :class:`ZodiacPosition` for the normalized degree.
    """
    deg = degree % 360.0
    sign_num = int(deg // 30)
    return ZodiacPosition(
        sign=SIGN_CODES[sign_num],
        sign_num=sign_num,
        position=deg % 30.0,
        element=SIGN_NUM_TO_ELEMENT[sign_num],
        quality=SIGN_NUM_TO_QUALITY[sign_num],
    )


def angle_degrees(subject: AstrologicalSubjectModel) -> Dict[str, Optional[float]]:
    """Return the absolute longitudes of the four chart angles.

    Args:
        subject: The chart to read.

    Returns:
        Mapping of angle name (Ascendant/Medium_Coeli/Descendant/Imum_Coeli) to
        its ``abs_pos`` in degrees, or ``None`` when the angle is absent (e.g.
        a chart built without a known birth time).
    """
    result: Dict[str, Optional[float]] = {}
    for public_name, attr in _ANGLE_ATTRS.items():
        point = getattr(subject, attr, None)
        result[public_name] = point.abs_pos if point is not None else None
    return result


def house_cusps(subject: AstrologicalSubjectModel) -> List[float]:
    """Return the twelve house-cusp longitudes in order 1..12.

    Args:
        subject: The chart to read.

    Returns:
        A list of twelve cusp longitudes suitable for
        :func:`kerykeion.utilities.get_planet_house`.
    """
    return [getattr(subject, attr).abs_pos for attr in _HOUSE_ATTRS]


def scoring_planets(subject: AstrologicalSubjectModel) -> List[KerykeionPointModel]:
    """Return the ten planets present on the subject (Sun … Pluto).

    Points that were not calculated for the chart (``None``) are skipped, so the
    caller can rely on every returned point being usable.

    Args:
        subject: The chart to read.

    Returns:
        The present planetary points, in canonical Sun-to-Pluto order.
    """
    points: List[KerykeionPointModel] = []
    for attr in _PLANET_ATTRS:
        point = getattr(subject, attr, None)
        if point is not None:
            points.append(point)
    return points


def part_of_fortune_degree(subject: AstrologicalSubjectModel) -> Optional[float]:
    """Return the Part of Fortune longitude, computing it if not pre-calculated.

    Prefers the subject's own ``pars_fortunae`` when present (so the value is
    consistent with the rest of the chart, including sidereal frames); otherwise
    derives it from the sect-sensitive lot formula — ``Asc + Moon - Sun`` by day,
    ``Asc + Sun - Moon`` by night — so the Almuten's fifth hylegiacal place is
    available for any chart with a known birth time.

    Args:
        subject: The chart to read.

    Returns:
        The Part of Fortune longitude in the subject's zodiac, or ``None`` when
        the Ascendant/Sun/Moon are unavailable (e.g. unknown birth time).
    """
    existing = getattr(subject, "pars_fortunae", None)
    if existing is not None:
        return existing.abs_pos

    ascendant, sun, moon = subject.ascendant, subject.sun, subject.moon
    if ascendant is None or sun is None or moon is None:
        return None

    if bool(getattr(subject, "is_diurnal", True)):
        degree = ascendant.abs_pos + moon.abs_pos - sun.abs_pos
    else:
        degree = ascendant.abs_pos + sun.abs_pos - moon.abs_pos
    return degree % 360.0


# =============================================================================
# RULERSHIP HELPERS
# =============================================================================


def sign_ruler(sign: Sign, rulers: Dict[Sign, List[str]] = MODERN_RULERS) -> List[str]:
    """Return the ruling planet(s) of a sign for the given rulership table.

    Args:
        sign: Three-letter sign code.
        rulers: Rulership table to use (defaults to the modern rulerships).

    Returns:
        The ruling planet name(s); an empty list if the sign is unknown.
    """
    return list(rulers.get(sign, []))


def rulers_inverse(rulers: Dict[Sign, List[str]] = MODERN_RULERS) -> Dict[str, List[Sign]]:
    """Invert a rulership table into planet -> signs it rules.

    Args:
        rulers: Sign -> ruler(s) table (defaults to the modern rulerships).

    Returns:
        Planet name -> list of signs that planet rules.
    """
    inverse: Dict[str, List[Sign]] = {}
    for sign, planets in rulers.items():
        for planet in planets:
            inverse.setdefault(planet, []).append(sign)
    return inverse


# =============================================================================
# ZODIAC-FRAME CONVERSION
# =============================================================================


def to_subject_zodiac(tropical_degree: float, subject: AstrologicalSubjectModel) -> float:
    """Convert a raw tropical longitude into the subject's zodiac frame.

    The ephemeris returns tropical longitudes; a sidereal chart measures signs
    from a precessed origin. Subtracting the chart's ayanamsa aligns a raw
    longitude with the sign boundaries the subject actually uses.

    Args:
        tropical_degree: A raw tropical longitude (e.g. from ``swe.calc_ut``).
        subject: The chart whose zodiac frame to match.

    Returns:
        The longitude in the subject's zodiac, normalized to ``[0, 360)``.
    """
    if getattr(subject, "zodiac_type", "Tropical") == "Sidereal" and subject.ayanamsa_value:
        return (tropical_degree - subject.ayanamsa_value) % 360.0
    return tropical_degree % 360.0


# =============================================================================
# PRENATAL SYZYGY
# =============================================================================
# The Sun-Moon elongation is a sawtooth (it wraps every synodic month), so a
# plain bracketless search over a wide window is unreliable. We instead (1) read
# the elongation at birth to know which syzygy is the most recent and roughly
# when it was, then (2) bracket a few days around that estimate — where the
# elongation IS monotonic — and bisect. This is self-contained and robust for
# any date the ephemeris covers.

#: Mean synodic month in days (Chapront ELP 2000-82B).
_SYNODIC_MONTH: float = 29.530588853

#: Mean daily growth of the Sun-Moon elongation (~12.19°/day).
_MEAN_DAILY_ELONGATION: float = 360.0 / _SYNODIC_MONTH


def _wrap_180(angle: float) -> float:
    """Wrap an angle into the signed range ``[-180, 180)``."""
    return (angle + 180.0) % 360.0 - 180.0


def _sun_moon_longitudes(julian_day: float) -> tuple[float, float]:
    """Return the (Sun, Moon) tropical ecliptic longitudes at a Julian Day.

    The caller must hold :data:`EPHEMERIS_LOCK`.
    """
    sun = float(swe.calc_ut(julian_day, swe.SUN, swe.FLG_SWIEPH)[0][0])
    moon = float(swe.calc_ut(julian_day, swe.MOON, swe.FLG_SWIEPH)[0][0])
    return sun, moon


def prenatal_syzygy(subject: AstrologicalSubjectModel) -> Optional[SyzygyInfo]:
    """Compute the prenatal syzygy — the New or Full Moon just before birth.

    The most recent of the preceding New Moon and the preceding Full Moon is the
    syzygy. We determine *which* it is directly from the elongation at birth (a
    waxing chart — elongation below 180° — was most recently preceded by a New
    Moon; otherwise by a Full Moon), estimate when that crossing happened, and
    refine it by bisection over a tight, monotonic bracket.

    The significant degree follows tradition: for a New Moon it is the
    conjunction degree (the Sun's longitude, equal to the Moon's); for a Full
    Moon it is the longitude of the luminary *above the horizon* at birth — the
    Sun for a day chart, the Moon for a night chart. The result is expressed in
    the subject's own zodiac so sign lookups are consistent for sidereal charts.

    All ephemeris access is guarded by :data:`EPHEMERIS_LOCK`, which the backend
    requires for its mutable global state.

    Args:
        subject: The chart to read (must carry a ``julian_day``).

    Returns:
        A :class:`SyzygyInfo`, or ``None`` when the birth Julian Day is missing
        or the ephemeris cannot resolve the lunation.
    """
    birth_jd = getattr(subject, "julian_day", None)
    if birth_jd is None:
        return None

    try:
        with EPHEMERIS_LOCK:
            configure_ephemeris_path()

            sun_birth, moon_birth = _sun_moon_longitudes(birth_jd)
            elongation = (moon_birth - sun_birth) % 360.0

            # Waxing (elongation < 180°) ⇒ the last syzygy was a New Moon;
            # waning ⇒ a Full Moon. This is always the more recent of the two.
            kind = "New" if elongation < 180.0 else "Full"
            target = 0.0 if kind == "New" else 180.0

            # Estimate how far back the elongation last equalled the target, then
            # bracket ±3 days (monotonic there) and bisect the signed offset.
            degrees_since = (elongation - target) % 360.0
            estimate_jd = birth_jd - degrees_since / _MEAN_DAILY_ELONGATION
            low, high = estimate_jd - 3.0, estimate_jd + 3.0

            for _ in range(60):
                mid = (low + high) / 2.0
                sun_mid, moon_mid = _sun_moon_longitudes(mid)
                offset = _wrap_180((moon_mid - sun_mid) - target)
                if offset < 0.0:
                    low = mid  # syzygy is later than mid
                else:
                    high = mid  # syzygy is at or before mid
                if high - low < 1e-7:
                    break

            syzygy_jd = (low + high) / 2.0
            sun_lon, moon_lon = _sun_moon_longitudes(syzygy_jd)
    except Exception as exc:
        # Any ephemeris failure (e.g. an out-of-range date raising the backend's
        # range error — which is NOT a RuntimeError) is non-fatal here: the
        # prenatal syzygy is an optional hylegiacal place, so we log and let the
        # Almuten drop it rather than propagate. Deliberately backend-agnostic
        # (libephemeris and swisseph raise different exception types).
        logger.debug("Prenatal syzygy skipped (ephemeris unavailable): %s", exc)
        return None

    is_diurnal = bool(getattr(subject, "is_diurnal", True))
    if kind == "New":
        raw_degree = sun_lon  # Sun and Moon coincide at the conjunction.
    else:  # Full Moon — use the luminary above the horizon at birth.
        raw_degree = sun_lon if is_diurnal else moon_lon

    return SyzygyInfo(
        degree=to_subject_zodiac(raw_degree, subject),
        kind=kind,
        julian_day=syzygy_jd,
    )
