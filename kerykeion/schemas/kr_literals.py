# -*- coding: utf-8 -*-
"""
This is part of Kerykeion (C) 2025 Giacomo Battaglia
"""

from typing import Literal
from typing_extensions import TypeAlias


ZodiacType: TypeAlias = Literal["Tropical", "Sidereal"]
"""Literal type for Zodiac Types"""


Sign: TypeAlias = Literal["Ari", "Tau", "Gem", "Can", "Leo", "Vir", "Lib", "Sco", "Sag", "Cap", "Aqu", "Pis"]
"""Literal type for Zodiac Signs"""


SignNumbers: TypeAlias = Literal[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
"""Literal type for Zodiac Sign Numbers, the signs are numbered in order starting from Aries (0) to Pis (11)"""


AspectMovementType: TypeAlias = Literal["Applying", "Separating", "Static"]
"""Literal type for Aspect Movement.

Values:
    - "Applying": planets are moving toward the exact aspect (orb decreasing).
    - "Separating": planets are moving away from the exact aspect (orb increasing).
    - "Static": both points are effectively motionless relative to one another, so the orb does not change over time.
"""


Houses: TypeAlias = Literal[
    "First_House",
    "Second_House",
    "Third_House",
    "Fourth_House",
    "Fifth_House",
    "Sixth_House",
    "Seventh_House",
    "Eighth_House",
    "Ninth_House",
    "Tenth_House",
    "Eleventh_House",
    "Twelfth_House",
]
"""Literal type for Houses"""


HouseNumbers: TypeAlias = Literal[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
"""Literal type for House Numbers, starting from the First House (1) to the Twelfth House (12)"""


AstrologicalPoint: TypeAlias = Literal[
    # Main Planets
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
    # Fixed Stars
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
    # Arabic Parts
    "Pars_Fortunae",
    "Pars_Spiritus",
    "Pars_Amoris",
    "Pars_Fidei",
    # Special Points
    "Vertex",
    "Anti_Vertex",
    # Axial Cusps
    "Ascendant",
    "Medium_Coeli",
    "Descendant",
    "Imum_Coeli",
]

"""Literal type for all astrological points supported by Kerykeion.

Includes planets, lunar nodes, special points, asteroids, trans-Neptunian objects,
fixed stars, Arabic parts (lots), angular points, and axial cusps.

Fixed Stars (23 total, expanded in v5.12 from 2):
    The original pair (Regulus, Spica) are joined by 21 additional stars
    chosen for their traditional astrological significance. The set includes
    all 15 Behenian stars of the medieval/Hermetic tradition.

    Royal Stars (Watchers of the sky in Persian/Hellenistic astrology):
        - Regulus (alpha Leonis) -- Watcher of the North, mag 1.35
        - Aldebaran (alpha Tauri) -- Watcher of the East, mag 0.87
        - Antares (alpha Scorpii) -- Watcher of the West, mag 1.06
        - Fomalhaut (alpha Piscis Austrini) -- Watcher of the South, mag 1.16

    Behenian stars (not listed above):
        - Algol (beta Persei), Sirius (alpha Canis Majoris),
          Procyon (alpha Canis Minoris), Capella (alpha Aurigae),
          Spica (alpha Virginis), Arcturus (alpha Bootis),
          Vega (alpha Lyrae), Alcyone (eta Tauri),
          Alphecca (alpha Coronae Borealis), Algorab (delta Corvi),
          Deneb Algedi (delta Capricorni), Alkaid (eta Ursae Majoris)

    Other prominent fixed stars:
        - Betelgeuse (alpha Orionis), Canopus (alpha Carinae),
          Pollux (beta Geminorum), Deneb (alpha Cygni),
          Altair (alpha Aquilae), Rigel (beta Orionis),
          Achernar (alpha Eridani)
"""


Element: TypeAlias = Literal["Air", "Fire", "Earth", "Water"]
"""Literal type for Elements"""


Quality: TypeAlias = Literal["Cardinal", "Fixed", "Mutable"]
"""Literal type for Qualities"""


ChartType: TypeAlias = Literal["Natal", "Synastry", "Transit", "Composite", "DualReturnChart", "SingleReturnChart"]
"""Literal type for Chart Types"""


PointType: TypeAlias = Literal["AstrologicalPoint", "House"]
"""Literal type for Point Types"""


LunarPhaseEmoji: TypeAlias = Literal["🌑", "🌒", "🌓", "🌔", "🌕", "🌖", "🌗", "🌘"]
"""Literal type for Lunar Phases Emoji"""


LunarPhaseName: TypeAlias = Literal[
    "New Moon",
    "Waxing Crescent",
    "First Quarter",
    "Waxing Gibbous",
    "Full Moon",
    "Waning Gibbous",
    "Last Quarter",
    "Waning Crescent",
]
"""Literal type for Lunar Phases Name"""


SiderealMode: TypeAlias = Literal[
    "FAGAN_BRADLEY",
    "LAHIRI",
    "DELUCE",
    "RAMAN",
    "USHASHASHI",
    "KRISHNAMURTI",
    "DJWHAL_KHUL",
    "YUKTESHWAR",
    "JN_BHASIN",
    "BABYL_KUGLER1",
    "BABYL_KUGLER2",
    "BABYL_KUGLER3",
    "BABYL_HUBER",
    "BABYL_ETPSC",
    "ALDEBARAN_15TAU",
    "HIPPARCHOS",
    "SASSANIAN",
    "J2000",
    "J1900",
    "B1950",
    # v5.12 additions
    "ARYABHATA",
    "ARYABHATA_522",
    "ARYABHATA_MSUN",
    "GALCENT_0SAG",
    "GALCENT_COCHRANE",
    "GALCENT_MULA_WILHELM",
    "GALCENT_RGILBRAND",
    "GALEQU_FIORENZA",
    "GALEQU_IAU1958",
    "GALEQU_MULA",
    "GALEQU_TRUE",
    "GALALIGN_MARDYKS",
    "KRISHNAMURTI_VP291",
    "LAHIRI_1940",
    "LAHIRI_ICRC",
    "LAHIRI_VP285",
    "SURYASIDDHANTA",
    "SURYASIDDHANTA_MSUN",
    "SS_CITRA",
    "SS_REVATI",
    "TRUE_CITRA",
    "TRUE_MULA",
    "TRUE_PUSHYA",
    "TRUE_REVATI",
    "TRUE_SHEORAN",
    "BABYL_BRITTON",
    "VALENS_MOON",
    # User-defined ayanamsa (requires custom_ayanamsa_t0 and custom_ayanamsa_ayan_t0)
    "USER",
]
"""Literal type for sidereal modes, also known as ayanamsa systems.

What is Ayanamsa?
    Ayanamsa (Sanskrit: ayanamsha) is the angular difference between the tropical
    zodiac (anchored to the vernal equinox) and the sidereal zodiac (anchored to
    fixed star positions). Due to the precession of the equinoxes (~50.3 arcseconds
    per year), the two zodiacs slowly diverge. Different ayanamsa systems disagree
    on the exact offset because they use different reference stars or epochs to
    define sidereal 0 Aries. As of 2025, most systems place the offset at roughly
    23-25 degrees.

Expanded in v5.12 from 20 to 47 named modes + USER (custom ayanamsa), 48 total.

Mode families:

    Indian / Vedic:
        LAHIRI (Indian government standard, ~23.85 deg in 2025),
        LAHIRI_1940, LAHIRI_ICRC, LAHIRI_VP285,
        KRISHNAMURTI (KP system, ~23.76 deg), KRISHNAMURTI_VP291,
        RAMAN, USHASHASHI, JN_BHASIN, YUKTESHWAR,
        ARYABHATA, ARYABHATA_522, ARYABHATA_MSUN,
        SURYASIDDHANTA, SURYASIDDHANTA_MSUN, SS_CITRA, SS_REVATI,
        TRUE_CITRA, TRUE_MULA, TRUE_PUSHYA, TRUE_REVATI, TRUE_SHEORAN

    Western sidereal:
        FAGAN_BRADLEY (default, ~24.74 deg in 2025 -- Cyril Fagan / Donald Bradley),
        DELUCE, DJWHAL_KHUL, HIPPARCHOS, SASSANIAN

    Babylonian:
        BABYL_KUGLER1, BABYL_KUGLER2, BABYL_KUGLER3,
        BABYL_HUBER, BABYL_ETPSC, BABYL_BRITTON

    Galactic alignment:
        GALCENT_0SAG, GALCENT_COCHRANE, GALCENT_MULA_WILHELM, GALCENT_RGILBRAND,
        GALEQU_FIORENZA, GALEQU_IAU1958, GALEQU_MULA, GALEQU_TRUE,
        GALALIGN_MARDYKS

    Reference frames:
        J2000, J1900, B1950

    Astronomical:
        ALDEBARAN_15TAU (fixes Aldebaran at 15 Taurus), VALENS_MOON

    User-defined:
        USER -- define a custom ayanamsa by specifying ``custom_ayanamsa_t0``
        (Julian Day of the reference epoch when tropical and sidereal zodiacs
        coincide) and ``custom_ayanamsa_ayan_t0`` (the ayanamsa offset in
        degrees at that epoch). The Swiss Ephemeris extrapolates for other
        dates using its precession model.
"""


HousesSystemIdentifier: TypeAlias = Literal[
    "A", "B", "C", "D", "F", "H", "I", "i", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y"
]
"""
Literal type for Houses Systems:

A = equal
B = Alcabitius
C = Campanus
D = equal (MC)
F = Carter poli-equ.
H = horizon/azimut
I = Sunshine
i = Sunshine/alt.
K = Koch
L = Pullen SD
M = Morinus
N = equal/1=Aries
O = Porphyry
P = Placidus
Q = Pullen SR
R = Regiomontanus
S = Sripati
T = Polich/Page
U = Krusinski-Pisa-Goelzer
V = equal/Vehlow
W = equal/whole sign
X = axial rotation system/Meridian houses
Y = APC houses

Usually the standard is Placidus (P)
"""


PerspectiveType: TypeAlias = Literal["Apparent Geocentric", "Heliocentric", "Topocentric", "True Geocentric"]
"""
Literal type for perspective types.
- "Apparent Geocentric": Earth-centered, apparent positions.
- "Heliocentric": Sun-centered.
- "Topocentric": Observer's location on Earth's surface.
- "True Geocentric": Earth-centered, true positions.

Usually the standard is "Apparent Geocentric"
"""


SignsEmoji: TypeAlias = Literal["♈️", "♉️", "♊️", "♋️", "♌️", "♍️", "♎️", "♏️", "♐️", "♑️", "♒️", "♓️"]
"""Literal type for Zodiac Signs Emoji"""

KerykeionChartTheme: TypeAlias = Literal[
    "light", "dark", "dark-high-contrast", "classic", "strawberry", "black-and-white"
]
"""Literal type for Kerykeion Chart Themes"""


KerykeionChartStyle: TypeAlias = Literal["classic", "modern"]
"""Literal type for Kerykeion Chart Styles"""


KerykeionChartLanguage: TypeAlias = Literal["EN", "FR", "PT", "IT", "CN", "ES", "RU", "TR", "DE", "HI"]
"""Literal type for Kerykeion Chart Languages"""


RelationshipScoreDescription: TypeAlias = Literal[
    "Minimal", "Medium", "Important", "Very Important", "Exceptional", "Rare Exceptional"
]
"""Literal type for Relationship Score Description"""


CompositeChartType: TypeAlias = Literal["Midpoint"]
"""Literal type for Composite Chart Types"""

AspectName: TypeAlias = Literal[
    "conjunction",
    "semi-sextile",
    "semi-square",
    "sextile",
    "quintile",
    "square",
    "trine",
    "sesquiquadrate",
    "biquintile",
    "quincunx",
    "opposition",
]
"""Literal type for all the available aspects names"""

ReturnType: TypeAlias = Literal["Lunar", "Solar"]
"""Literal type for Return Types"""


# ---------------------------------------------------------------------------
# Deprecated aliases for backward compatibility with Kerykeion v4.x
# ---------------------------------------------------------------------------
# These will be removed in v6.0 - migrate to AstrologicalPoint
Planet: TypeAlias = AstrologicalPoint
"""DEPRECATED: Use AstrologicalPoint instead. This alias will be removed in v6.0."""

AxialCusps: TypeAlias = AstrologicalPoint
"""DEPRECATED: Use AstrologicalPoint instead. This alias will be removed in v6.0."""
