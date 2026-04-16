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


TRADITIONAL_ASTROLOGY_ACTIVE_POINTS: list[AstrologicalPoint] = [
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

DEFAULT_ACTIVE_POINTS: list[AstrologicalPoint] = [
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
    # --- Fixed Stars (23 total, expanded in v5.12 from 2) ---
    # "Regulus",
    # "Spica",
    # "Aldebaran",
    # "Antares",
    # "Sirius",
    # "Fomalhaut",
    # "Algol",
    # "Betelgeuse",
    # "Canopus",
    # "Procyon",
    # "Arcturus",
    # "Pollux",
    # "Deneb",
    # "Altair",
    # "Rigel",
    # "Achernar",
    # "Capella",
    # "Vega",
    # "Alcyone",
    # "Alphecca",
    # "Algorab",
    # "Deneb_Algedi",
    # "Alkaid",
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

ALL_ACTIVE_POINTS: list[AstrologicalPoint] = [
    # Planets
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
    # Lunar Nodes
    "Mean_North_Lunar_Node",
    "True_North_Lunar_Node",
    "Mean_South_Lunar_Node",
    "True_South_Lunar_Node",
    # Special Points
    "Chiron",
    "Mean_Lilith",
    "True_Lilith",
    "Earth",
    "Pholus",
    # Asteroids
    "Ceres",
    "Pallas",
    "Juno",
    "Vesta",
    # Trans-Neptunian Objects
    "Eris",
    "Sedna",
    "Haumea",
    "Makemake",
    "Ixion",
    "Orcus",
    "Quaoar",
    # Fixed Stars (23 total -- expanded in v5.12 from 2)
    "Regulus",
    "Spica",
    "Aldebaran",
    "Antares",
    "Sirius",
    "Fomalhaut",
    "Algol",
    "Betelgeuse",
    "Canopus",
    "Procyon",
    "Arcturus",
    "Pollux",
    "Deneb",
    "Altair",
    "Rigel",
    "Achernar",
    "Capella",
    "Vega",
    "Alcyone",
    "Alphecca",
    "Algorab",
    "Deneb_Algedi",
    "Alkaid",
    # Angular Points
    "Ascendant",
    "Medium_Coeli",
    "Descendant",
    "Imum_Coeli",
    "Vertex",
    "Anti_Vertex",
    # Uranian / Hamburg School hypothetical planets
    "Cupido",
    "Hades",
    "Zeus",
    "Kronos",
    "Apollon",
    "Admetos",
    "Vulkanus",
    "Poseidon",
    # Lilith/Priapus variants
    "Interpolated_Lilith",
    "Mean_Priapus",
    "True_Priapus",
    # Lunar apse points
    "Interpolated_Perigee",
    "White_Moon",
    # Arabic Parts (Lots)
    "Pars_Fortunae",
    "Pars_Spiritus",
    "Pars_Amoris",
    "Pars_Fidei",
]
"""
Full list of active points in the charts or aspects calculations.
The full list of points is available in the `schemas.kr_literals.AstrologicalPoint` literal.
"""

# =============================================================================
# FIXED STAR PRESETS (v6.0)
# =============================================================================
# Use these with the `active_fixed_stars` parameter of AstrologicalSubjectFactory.
# Names must match entries in the Swiss Ephemeris sefstars.txt catalog.

ROYAL_FIXED_STARS: list[str] = [
    "Aldebaran",
    "Regulus",
    "Antares",
    "Fomalhaut",
]
"""The four Royal Stars (Watchers of the Sky) in Persian/Hellenistic astrology."""

BEHENIAN_FIXED_STARS: list[str] = [
    "Algol",
    "Alcyone",
    "Aldebaran",
    "Capella",
    "Sirius",
    "Procyon",
    "Regulus",
    "Algorab",
    "Spica",
    "Arcturus",
    "Alphecca",
    "Antares",
    "Vega",
    "Deneb Algedi",
    "Fomalhaut",
]
"""The 15 Behenian stars of the medieval/Hermetic magical tradition."""

DEFAULT_FIXED_STARS: list[str] = [
    "Regulus",
    "Spica",
    "Aldebaran",
    "Antares",
    "Sirius",
    "Fomalhaut",
    "Algol",
    "Betelgeuse",
    "Canopus",
    "Procyon",
    "Arcturus",
    "Pollux",
    "Deneb",
    "Altair",
    "Rigel",
    "Achernar",
    "Capella",
    "Vega",
    "Alcyone",
    "Alphecca",
    "Algorab",
    "Deneb Algedi",
    "Alkaid",
]
"""The 23 default fixed stars (same set as Kerykeion v5.12)."""


URANIAN_ACTIVE_POINTS: list[AstrologicalPoint] = [
    "Cupido",
    "Hades",
    "Zeus",
    "Kronos",
    "Apollon",
    "Admetos",
    "Vulkanus",
    "Poseidon",
]
"""
Uranian / Hamburg School hypothetical trans-Neptunian planets (Alfred Witte).
Use these alongside DEFAULT_ACTIVE_POINTS for Uranian astrology work.
"""


DEFAULT_ACTIVE_ASPECTS: list[ActiveAspect] = [
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

ALL_ACTIVE_ASPECTS: list[ActiveAspect] = [
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

DISCEPOLO_SCORE_ACTIVE_ASPECTS: list[ActiveAspect] = [
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


# =============================================================================
# POINT ID MAPPINGS (Swiss Ephemeris)
# =============================================================================
# Centralized celestial point name -> Swiss Ephemeris ID mappings.
# Previously duplicated in `utilities.py` (_POINT_NUMBER_MAP) and
# `astrological_subject_factory.py` (STANDARD_PLANETS); unified here to
# eliminate drift between the two. Historic symbols remain re-exported in
# those modules for backward compatibility.

STANDARD_PLANETS: dict[AstrologicalPoint, int] = {
    "Sun": 0,
    "Moon": 1,
    "Mercury": 2,
    "Venus": 3,
    "Mars": 4,
    "Jupiter": 5,
    "Saturn": 6,
    "Uranus": 7,
    "Neptune": 8,
    "Pluto": 9,
    "Mean_North_Lunar_Node": 10,
    "True_North_Lunar_Node": 11,
    "Mean_Lilith": 12,
    "True_Lilith": 13,
    "Earth": 14,
    "Chiron": 15,
    "Pholus": 16,
    "Ceres": 17,
    "Pallas": 18,
    "Juno": 19,
    "Vesta": 20,
    # Interpolated lunar apse points (SwissEph IDs 21-22)
    "Interpolated_Lilith": 21,  # SE_INTP_APOG -- proper interpolated apogee
    "Interpolated_Perigee": 22,  # SE_INTP_PERG -- proper interpolated perigee
    # Uranian / Hamburg School hypothetical planets (SwissEph IDs 40-47)
    "Cupido": 40,
    "Hades": 41,
    "Zeus": 42,
    "Kronos": 43,
    "Apollon": 44,
    "Admetos": 45,
    "Vulkanus": 46,
    "Poseidon": 47,
}
"""
Standard planets with direct Swiss Ephemeris IDs (0-22, 40-47).
Used for `swe.calc_ut()` calls where the planet identifier is a native SE code.
"""

POINT_NUMBER_MAP: dict[str, int] = {
    **STANDARD_PLANETS,
    # Extra points without Swiss Ephemeris IDs
    "Mean_South_Lunar_Node": 1000,
    "True_South_Lunar_Node": 1100,
    "White_Moon": 56,  # SE_WHITE_MOON / Selena
    "Ascendant": 9900,
    "Descendant": 9901,
    "Medium_Coeli": 9902,
    "Imum_Coeli": 9903,
}
"""
Full mapping of astrological point names to Swiss Ephemeris IDs, including
synthetic IDs (>=1000) for points that don't have a native SE identifier
(South Nodes, axial cusps, White Moon).
"""

MAIN_PLANETS: list[AstrologicalPoint] = [
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
]
"""The ten main planets (Sun, Moon, Mercury..Pluto) in canonical report order."""

LUNAR_NODES: list[AstrologicalPoint] = [
    "Mean_North_Lunar_Node",
    "True_North_Lunar_Node",
]
"""North lunar nodes (mean and true). South nodes are derived via OPPOSITE_PAIRS."""

AXIAL_POINTS: list[AstrologicalPoint] = [
    "Ascendant",
    "Medium_Coeli",
    "Descendant",
    "Imum_Coeli",
]
"""The four axial cusps (angles) of the horoscope."""
