"""
Kerykeion Configuration Constants
=================================

This module contains all configuration constants used throughout the library.
These constants provide centralized, reusable values for:
- Zodiac and perspective types
- Chart types
- Default location values
- Aspect configurations
- Mathematical constants

Using these constants instead of magic strings/numbers improves maintainability
and reduces the risk of typos.
"""

from kerykeion.schemas.kr_literals import AstrologicalPoint
from kerykeion.schemas.kr_models import ActiveAspect
from typing import List


# =============================================================================
# ZODIAC TYPE CONSTANTS
# =============================================================================

ZODIAC_TYPE_TROPICAL: str = "Tropical"
"""Western zodiac based on seasons and the vernal equinox."""

ZODIAC_TYPE_SIDEREAL: str = "Sidereal"
"""Vedic/Eastern zodiac based on fixed star positions."""


# =============================================================================
# PERSPECTIVE TYPE CONSTANTS
# =============================================================================

PERSPECTIVE_APPARENT_GEOCENTRIC: str = "Apparent Geocentric"
"""Earth-centered view with atmospheric refraction correction (default)."""

PERSPECTIVE_TRUE_GEOCENTRIC: str = "True Geocentric"
"""Earth-centered view without refraction correction."""

PERSPECTIVE_HELIOCENTRIC: str = "Heliocentric"
"""Sun-centered view of planetary positions."""

PERSPECTIVE_TOPOCENTRIC: str = "Topocentric"
"""Observer location-centered view with parallax correction."""


# =============================================================================
# CHART TYPE CONSTANTS
# =============================================================================

CHART_TYPE_NATAL: str = "Natal"
"""Single birth/event chart."""

CHART_TYPE_TRANSIT: str = "Transit"
"""Dual chart comparing natal to current planetary positions."""

CHART_TYPE_SYNASTRY: str = "Synastry"
"""Dual chart comparing two individuals for compatibility."""

CHART_TYPE_COMPOSITE: str = "Composite"
"""Midpoint relationship chart."""

CHART_TYPE_SINGLE_RETURN: str = "SingleReturnChart"
"""Single planetary return chart (Solar or Lunar)."""

CHART_TYPE_DUAL_RETURN: str = "DualReturnChart"
"""Dual chart with natal and return overlay."""


# =============================================================================
# DEFAULT LOCATION CONSTANTS
# =============================================================================

DEFAULT_CITY: str = "Greenwich"
"""Default city for charts when location is not specified."""

DEFAULT_NATION: str = "GB"
"""Default country code (ISO 3166-1 alpha-2)."""

DEFAULT_TIMEZONE: str = "Etc/GMT"
"""Default timezone string."""

DEFAULT_LATITUDE: float = 51.5074
"""Default latitude (Greenwich Observatory)."""

DEFAULT_LONGITUDE: float = 0.0
"""Default longitude (Prime Meridian)."""


# =============================================================================
# MATHEMATICAL CONSTANTS
# =============================================================================

DEGREES_FULL_CIRCLE: int = 360
"""Degrees in a complete circle."""

DEGREES_HALF_CIRCLE: int = 180
"""Degrees in a semicircle (opposition)."""

DEGREES_PER_SIGN: int = 30
"""Degrees per zodiac sign."""

LUNAR_PHASES_COUNT: int = 28
"""Number of lunar phases/mansions in a complete cycle."""


# =============================================================================
# ASPECT DEGREE CONSTANTS
# =============================================================================

ASPECT_DEGREE_CONJUNCTION: int = 0
"""Conjunction aspect: planets at same position."""

ASPECT_DEGREE_SEMI_SEXTILE: int = 30
"""Semi-sextile aspect: 30 degrees apart."""

ASPECT_DEGREE_SEMI_SQUARE: int = 45
"""Semi-square aspect: 45 degrees apart."""

ASPECT_DEGREE_SEXTILE: int = 60
"""Sextile aspect: 60 degrees apart."""

ASPECT_DEGREE_QUINTILE: int = 72
"""Quintile aspect: 72 degrees apart."""

ASPECT_DEGREE_SQUARE: int = 90
"""Square aspect: 90 degrees apart."""

ASPECT_DEGREE_TRINE: int = 120
"""Trine aspect: 120 degrees apart."""

ASPECT_DEGREE_SESQUIQUADRATE: int = 135
"""Sesquiquadrate aspect: 135 degrees apart."""

ASPECT_DEGREE_BIQUINTILE: int = 144
"""Biquintile aspect: 144 degrees apart."""

ASPECT_DEGREE_QUINCUNX: int = 150
"""Quincunx/inconjunct aspect: 150 degrees apart."""

ASPECT_DEGREE_OPPOSITION: int = 180
"""Opposition aspect: 180 degrees apart."""


# =============================================================================
# HOUSE SYSTEM IDENTIFIERS
# =============================================================================

HOUSE_SYSTEM_PLACIDUS: str = "P"
"""Placidus house system (most common in Western astrology)."""

HOUSE_SYSTEM_KOCH: str = "K"
"""Koch house system."""

HOUSE_SYSTEM_WHOLE_SIGN: str = "W"
"""Whole Sign house system (traditional/Hellenistic)."""

HOUSE_SYSTEM_CAMPANUS: str = "C"
"""Campanus house system."""

HOUSE_SYSTEM_REGIOMONTANUS: str = "R"
"""Regiomontanus house system."""

HOUSE_SYSTEM_EQUAL: str = "E"
"""Equal house system (from Ascendant)."""

HOUSE_SYSTEM_MORINUS: str = "M"
"""Morinus house system."""


# =============================================================================
# ELEMENT AND QUALITY CONSTANTS
# =============================================================================

ELEMENT_FIRE: str = "Fire"
ELEMENT_EARTH: str = "Earth"
ELEMENT_AIR: str = "Air"
ELEMENT_WATER: str = "Water"

QUALITY_CARDINAL: str = "Cardinal"
QUALITY_FIXED: str = "Fixed"
QUALITY_MUTABLE: str = "Mutable"


# =============================================================================
# ACTIVE POINTS CONFIGURATIONS
# =============================================================================


TRADITIONAL_ASTROLOGY_ACTIVE_POINTS: List[AstrologicalPoint] = [
    "Sun",
    "Moon",
    "Mercury",
    "Venus",
    "Mars",
    "Jupiter",
    "Saturn",
    "True_North_Lunar_Node",
    "True_South_Lunar_Node",
]
"""
Traditional astrology active points: the seven classical planets (Sun to Saturn) plus lunar nodes.
Excludes modern planets (Uranus, Neptune, Pluto), asteroids, and calculated points (Asc, MC, etc.).
"""

DEFAULT_ACTIVE_POINTS: List[AstrologicalPoint] = [
    "Sun",
    "Moon",
    "Mercury",
    "Venus",
    "Mars",
    "Jupiter",
    "Saturn",
    "Uranus",
    "Neptune",
    "Pluto",
    # "Mean_North_Lunar_Node",
    "True_North_Lunar_Node",
    # "Mean_South_Lunar_Node",
    "True_South_Lunar_Node",
    "Chiron",
    "Mean_Lilith",
    # "True_Lilith",
    # "Earth",
    # "Pholus",
    # "Ceres",
    # "Pallas",
    # "Juno",
    # "Vesta",
    # "Eris",
    # "Sedna",
    # "Haumea",
    # "Makemake",
    # "Ixion",
    # "Orcus",
    # "Quaoar",
    # "Regulus",
    # "Spica",
    "Ascendant",
    "Medium_Coeli",
    "Descendant",
    "Imum_Coeli",
    # "Vertex",
    # "Anti_Vertex",
    # "Pars_Fortunae",
    # "Pars_Spiritus",
    # "Pars_Amoris",
    # "Pars_Fidei"
]
"""
Default list of active points in the charts or aspects calculations.
The full list of points is available in the `schemas.kr_literals.AstrologicalPoint` literal.
"""

ALL_ACTIVE_POINTS: List[AstrologicalPoint] = [
    "Sun",
    "Moon",
    "Mercury",
    "Venus",
    "Mars",
    "Jupiter",
    "Saturn",
    "Uranus",
    "Neptune",
    "Pluto",
    "Mean_North_Lunar_Node",
    "True_North_Lunar_Node",
    "Mean_South_Lunar_Node",
    "True_South_Lunar_Node",
    "Chiron",
    "Mean_Lilith",
    "True_Lilith",
    "Earth",
    "Pholus",
    "Ceres",
    "Pallas",
    "Juno",
    "Vesta",
    "Eris",
    "Sedna",
    "Haumea",
    "Makemake",
    "Ixion",
    "Orcus",
    "Quaoar",
    "Regulus",
    "Spica",
    "Ascendant",
    "Medium_Coeli",
    "Descendant",
    "Imum_Coeli",
    "Vertex",
    "Anti_Vertex",
    "Pars_Fortunae",
    "Pars_Spiritus",
    "Pars_Amoris",
    "Pars_Fidei",
]
"""
Full list of active points in the charts or aspects calculations.
The full list of points is available in the `schemas.kr_literals.AstrologicalPoint` literal.
"""

DEFAULT_ACTIVE_ASPECTS: List[ActiveAspect] = [
    {"name": "conjunction", "orb": 10},
    {"name": "opposition", "orb": 10},
    {"name": "trine", "orb": 8},
    {"name": "sextile", "orb": 6},
    {"name": "square", "orb": 5},
    {"name": "quintile", "orb": 1},
    # {"name": "semi-sextile", "orb": 1},
    # {"name": "semi-square", "orb": 1},
    # {"name": "sesquiquadrate", "orb": 1},
    # {"name": "biquintile", "orb": 1},
    # {"name": "quincunx", "orb": 1},
]
"""
Default list of active aspects in the aspects calculations.
The full list of aspects is available in the `schemas.kr_literals.AspectName` literal.
"""

ALL_ACTIVE_ASPECTS: List[ActiveAspect] = [
    {"name": "conjunction", "orb": 10},
    {"name": "opposition", "orb": 10},
    {"name": "trine", "orb": 8},
    {"name": "sextile", "orb": 6},
    {"name": "square", "orb": 5},
    {"name": "quintile", "orb": 1},
    {"name": "semi-sextile", "orb": 1},
    {"name": "semi-square", "orb": 1},
    {"name": "sesquiquadrate", "orb": 1},
    {"name": "biquintile", "orb": 1},
    {"name": "quincunx", "orb": 1},
]
"""
Full list of active aspects in the charts or aspects calculations.
The full list of aspects is available in the `schemas.kr_literals.AspectName` literal.
"""

DISCEPOLO_SCORE_ACTIVE_ASPECTS: List[ActiveAspect] = [
    {"name": "conjunction", "orb": 8},
    {"name": "semi-sextile", "orb": 2},
    {"name": "semi-square", "orb": 2},
    {"name": "sextile", "orb": 4},
    {"name": "square", "orb": 5},
    {"name": "trine", "orb": 7},
    {"name": "sesquiquadrate", "orb": 2},
    {"name": "opposition", "orb": 8},
]
"""
List of active aspects with their orbs according to Ciro Discepolo's affinity scoring methodology.
"""
