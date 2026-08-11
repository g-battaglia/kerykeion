# -*- coding: utf-8 -*-
"""
Reference tables and tunable constants for the dominants calculator.
====================================================================

This module is the single place where every weight, threshold and lookup table
used by the dominant-calculation schools lives. Keeping the numbers separate
from the algorithms makes each school auditable at a glance and lets advanced
users fork a strategy with different calibration without touching logic.

Sources / lineage:
    - Modern weighted method: the criteria publicly described by Astrotheme
      (angularity, aspect activity, dignity, rulership). The exact point values
      Astrotheme uses are proprietary, so the constants below are a transparent,
      well-documented approximation — tune them freely.
    - Almuten Figuris: Ptolemaic essential dignities (domicile 5, exaltation 4,
      triplicity 3, term 2, face 1) tallied over the five hylegiacal places, as
      documented on kerykeion.net. Accidental-dignity values follow common
      traditional schemes and are an *optional* layer.

This is part of Kerykeion (C) 2025 Giacomo Battaglia
"""

from __future__ import annotations

from typing import Dict, List, Tuple

from kerykeion.schemas.literals import Element, Quality, Sign
from kerykeion.schemas.models import ActiveAspect

# =============================================================================
# ZODIAC: SIGN INDEX -> ELEMENT / QUALITY (Title-case)
# =============================================================================
# Indexed by ``sign_num`` (0 = Aries … 11 = Pisces). Title-case so the values
# match the ``Element`` / ``Quality`` literals AND the keys of the dignity
# tables (e.g. ``TRIPLICITY_RULERS["Fire"]``). A separate lowercase mapping
# already exists under ``charts/`` for the chart drawer; we keep a Title-case
# copy here to stay decoupled from the rendering package.

#: Element of each zodiac sign, indexed by ``sign_num`` (0-11).
SIGN_NUM_TO_ELEMENT: Tuple[Element, ...] = (
    "Fire",  # Aries
    "Earth",  # Taurus
    "Air",  # Gemini
    "Water",  # Cancer
    "Fire",  # Leo
    "Earth",  # Virgo
    "Air",  # Libra
    "Water",  # Scorpio
    "Fire",  # Sagittarius
    "Earth",  # Capricorn
    "Air",  # Aquarius
    "Water",  # Pisces
)

#: Quality (modality) of each zodiac sign, indexed by ``sign_num`` (0-11).
SIGN_NUM_TO_QUALITY: Tuple[Quality, ...] = (
    "Cardinal",  # Aries
    "Fixed",  # Taurus
    "Mutable",  # Gemini
    "Cardinal",  # Cancer
    "Fixed",  # Leo
    "Mutable",  # Virgo
    "Cardinal",  # Libra
    "Fixed",  # Scorpio
    "Mutable",  # Sagittarius
    "Cardinal",  # Capricorn
    "Fixed",  # Aquarius
    "Mutable",  # Pisces
)

#: Polarity (Yang/Yin) of each element. Fire & Air are Yang (active,
#: extrovert); Earth & Water are Yin (receptive, introvert).
POLARITY_BY_ELEMENT: Dict[Element, str] = {
    "Fire": "Yang",
    "Air": "Yang",
    "Earth": "Yin",
    "Water": "Yin",
}

#: Map the lowercase element keys returned by ``calculate_element_points`` to
#: the Title-case ``Element`` literal used by the public models.
ELEMENT_LOWER_TO_TITLE: Dict[str, Element] = {
    "fire": "Fire",
    "earth": "Earth",
    "air": "Air",
    "water": "Water",
}

#: Map the lowercase modality keys returned by ``calculate_quality_points`` to
#: the Title-case ``Quality`` literal used by the public models.
QUALITY_LOWER_TO_TITLE: Dict[str, Quality] = {
    "cardinal": "Cardinal",
    "fixed": "Fixed",
    "mutable": "Mutable",
}


# =============================================================================
# RULERSHIP — MODERN (used by the modern weighted method)
# =============================================================================
# The traditional rulerships live in ``kerykeion.dignities.dignity_data`` and
# are consumed verbatim by the dignity engine and the Almuten Figuris. The
# modern weighted method instead assigns the outer planets as rulers of the
# three signs they are commonly given in modern practice, so we keep a separate
# MODERN map here (and never pollute the traditional one).

#: Sign -> modern ruling planet(s). Differs from the traditional table only for
#: Scorpio (Pluto), Aquarius (Uranus) and Pisces (Neptune).
MODERN_RULERS: Dict[Sign, List[str]] = {
    "Ari": ["Mars"],
    "Tau": ["Venus"],
    "Gem": ["Mercury"],
    "Can": ["Moon"],
    "Leo": ["Sun"],
    "Vir": ["Mercury"],
    "Lib": ["Venus"],
    "Sco": ["Pluto"],
    "Sag": ["Jupiter"],
    "Cap": ["Saturn"],
    "Aqu": ["Uranus"],
    "Pis": ["Neptune"],
}


# =============================================================================
# CLASSICAL PLANETS & PLANETARY DAY RULERS
# =============================================================================

#: The seven classical planets, in traditional (Chaldean, slowest-first) weight
#: order. Used as the candidate set for the Almuten Figuris and as the final,
#: deterministic tie-break order (earlier = wins a tie).
ALMUTEN_TIEBREAK_ORDER: Tuple[str, ...] = ("Saturn", "Jupiter", "Mars", "Sun", "Venus", "Mercury", "Moon")

#: The seven classical planets in luminary-first order (the candidate set used
#: when tallying dignities). Membership matches ``dignity_data.DIGNITY_PLANETS``.
CLASSICAL_PLANETS: Tuple[str, ...] = ("Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn")

#: Planetary ruler of each weekday, numbered 0 = Sunday … 6 = Saturday to match
#: the ``(int(jd + 0.5) + 1) % 7`` convention. Used for the optional Almuten
#: day-ruler accidental bonus.
WEEKDAY_RULERS: Tuple[str, ...] = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")


# =============================================================================
# MODERN WEIGHTED METHOD — ANGULARITY
# =============================================================================

#: Maximum orb (degrees) within which a planet is considered "angular". Beyond
#: this distance from an angle the angularity contribution is zero. Astrotheme
#: documents 15° as the distance at which the influence starts to manifest.
ANGULARITY_ORB: float = 15.0

#: Points awarded to a planet exactly conjunct the *Ascendant* (the strongest
#: angle). Other angles scale this down via ``ANGLE_WEIGHTS`` and the orb falls
#: off linearly to zero at ``ANGULARITY_ORB``.
ANGULARITY_MAX_POINTS: float = 4.0

#: Relative strength of each of the four angles, in decreasing order
#: Asc > MC > Desc > IC (per Astrotheme's documented hierarchy).
ANGLE_WEIGHTS: Dict[str, float] = {
    "Ascendant": 1.00,
    "Medium_Coeli": 0.80,
    "Descendant": 0.60,
    "Imum_Coeli": 0.50,
}


# =============================================================================
# MODERN WEIGHTED METHOD — ASPECT ACTIVITY
# =============================================================================

#: Base scale applied to every aspect contribution before the type/orb/pair
#: multipliers. Larger values make the chart's aspect network weigh more in the
#: planetary totals relative to angularity and rulership.
ASPECT_BASE_POINTS: float = 3.0

#: Extra multiplier when one of the two bodies of an aspect is a chart angle
#: (Asc/MC/Desc/IC). Aspects to the angles are emphasised, as in Astrotheme.
ASPECT_TO_ANGLE_MULTIPLIER: float = 1.5

#: Strength of each aspect *type*, keyed by its exact degree (matches
#: ``AspectModel.aspect_degrees``). Conjunction is strongest, then the soft/hard
#: majors, then the minors. Tune to taste.
ASPECT_STRENGTH: Dict[int, float] = {
    0: 1.00,  # conjunction
    180: 0.85,  # opposition
    120: 0.85,  # trine
    90: 0.60,  # square
    60: 0.50,  # sextile
    150: 0.30,  # quincunx (inconjunct)
    45: 0.20,  # semi-square
    135: 0.20,  # sesquiquadrate
    30: 0.15,  # semi-sextile
    72: 0.15,  # quintile
    144: 0.15,  # biquintile
}

#: Active aspects (name + orb) fed to ``AspectsFactory.single_chart_aspects``
#: for the modern method. Orbs are deliberately generous because we are
#: measuring overall *activity*, not drawing a chart. Each orb is also the
#: denominator of the orb-exactitude term (tighter aspect ⇒ larger weight).
DOMINANT_ASPECTS: List[ActiveAspect] = [
    {"name": "conjunction", "orb": 10.0},
    {"name": "opposition", "orb": 10.0},
    {"name": "trine", "orb": 8.0},
    {"name": "square", "orb": 8.0},
    {"name": "sextile", "orb": 6.0},
    {"name": "quincunx", "orb": 3.0},
    {"name": "semi-sextile", "orb": 2.0},
    {"name": "semi-square", "orb": 2.0},
    {"name": "sesquiquadrate", "orb": 2.0},
    {"name": "quintile", "orb": 2.0},
    {"name": "biquintile", "orb": 2.0},
]

#: Per-aspect orb lookup derived from ``DOMINANT_ASPECTS`` (name -> orb), used as
#: the orb-exactitude denominator.
ASPECT_ORB_BY_NAME: Dict[str, float] = {str(a["name"]): float(a["orb"]) for a in DOMINANT_ASPECTS}

#: Static "speed tier" of each body: fast bodies (Moon, inner planets) carry more
#: weight than slow ones, so a generational Neptune-Pluto aspect counts far less
#: than a personal Moon-Mars aspect. This is a *doctrinal* weight on the body's
#: nature, NOT the chart's instantaneous speed (speed/retrogradation are
#: deliberately excluded from the modern scoring).
PLANET_SPEED_TIER: Dict[str, float] = {
    "Moon": 1.00,
    "Mercury": 0.90,
    "Venus": 0.90,
    "Sun": 0.90,
    "Mars": 0.80,
    "Jupiter": 0.60,
    "Saturn": 0.55,
    "Uranus": 0.35,
    "Neptune": 0.30,
    "Pluto": 0.30,
    "Ascendant": 0.90,
    "Medium_Coeli": 0.90,
    "Descendant": 0.90,
    "Imum_Coeli": 0.90,
    "Mean_North_Lunar_Node": 0.40,
    "True_North_Lunar_Node": 0.40,
    "Chiron": 0.40,
}

#: Fallback speed tier for any body not listed above (asteroids, TNOs, etc.).
PLANET_SPEED_TIER_DEFAULT: float = 0.30


# =============================================================================
# MODERN WEIGHTED METHOD — ESSENTIAL DIGNITY (deliberately MILD)
# =============================================================================
# Astrotheme applies only a small bonus/penalty for dignity so it never
# distorts the result. We therefore map the dignity *label* to a small value
# instead of using the raw Ptolemaic score (which ranges -5..+5).
#
# Application (see ``ModernDominantStrategy._dignity_scores``): the planet's
# HIGHEST dignity supplies the bonus, while the Detriment/Fall penalties are
# applied ADDITIVELY on top of it whenever the debility holds. Dignities and
# debilities are independent, so a minor dignity never masks a debility:
# Mars at 28° Libra (own Egyptian term, in detriment) scores 0.25 - 1.00 =
# -0.75, and Mercury at 17° Pisces (own term, in detriment AND fall) scores
# 0.25 - 1.00 - 0.75 = -1.50.

#: Mild bonus/penalty by essential-dignity label.
DIGNITY_BONUS: Dict[str, float] = {
    "Domicile": 1.00,
    "Exaltation": 0.75,
    "Triplicity": 0.40,
    "Term": 0.25,
    "Face": 0.15,
    "Peregrine": 0.00,
    "Detriment": -1.00,
    "Fall": -0.75,
}


# =============================================================================
# MODERN WEIGHTED METHOD — RULERSHIP BONUS
# =============================================================================
# The ruler of the Ascendant is the single most important planet of a chart;
# the rulers of the MC, the Sun sign and the Moon sign follow in decreasing
# importance.

RULER_BONUS_ASC: float = 3.0
RULER_BONUS_MC: float = 2.0
RULER_BONUS_SUN_SIGN: float = 1.5
RULER_BONUS_MOON_SIGN: float = 1.0


# =============================================================================
# MODERN WEIGHTED METHOD — DERIVATION THRESHOLDS
# =============================================================================

#: How many top-scoring planets are flagged as "dominant".
DOMINANT_PLANET_COUNT: int = 3

#: How many top entries are flagged dominant in the sign and house categories.
DOMINANT_SIGN_COUNT: int = 3
DOMINANT_HOUSE_COUNT: int = 3

#: Flat weight added to the Ascendant's own sign when deriving dominant signs,
#: so the rising sign is always prominent.
ASC_SIGN_BONUS: float = 3.0


# =============================================================================
# ALMUTEN FIGURIS — ESSENTIAL & ACCIDENTAL DIGNITIES
# =============================================================================

#: Points for each essential dignity, summed across the five hylegiacal places.
ESSENTIAL_DIGNITY_POINTS: Dict[str, int] = {
    "Domicile": 5,
    "Exaltation": 4,
    "Triplicity": 3,
    "Term": 2,
    "Face": 1,
}

#: The five hylegiacal places evaluated, in canonical order. ``Pars_Fortunae``
#: and ``Syzygy`` may be unavailable (unknown birth time, ephemeris gap) and are
#: then skipped — the tally simply runs over the remaining places.
ALMUTEN_PLACES: Tuple[str, ...] = ("Sun", "Moon", "Ascendant", "Pars_Fortunae", "Syzygy")

#: OPTIONAL accidental-dignity points by house of residence (a common
#: traditional scheme). Only applied when ``include_accidental_dignities=True``.
ALMUTEN_HOUSE_PLACEMENT_POINTS: Dict[int, int] = {
    1: 12,
    10: 11,
    7: 10,
    4: 9,
    11: 8,
    5: 7,
    2: 6,
    9: 5,
    8: 4,
    3: 3,
    12: 2,
    6: 1,
}

#: OPTIONAL bonus for the planet ruling the weekday of birth.
ALMUTEN_DAY_RULER_BONUS: float = 7.0
