"""
Comprehensive Test Subject Matrix for Kerykeion

This module defines the test subjects used across the entire test suite.
It provides coverage for:
- Temporal range: 500 BC to 2200 AD (2700+ years)
- Geographic range: All latitudes from 66°S to 66°N
- All house systems (16+)
- All sidereal modes (20)
- Multiple synastry pairs

Generated data for these subjects is stored in expected_positions.py and expected_aspects.py.

Usage:
    from tests.data.test_subjects_matrix import TEMPORAL_SUBJECTS, GEOGRAPHIC_SUBJECTS
"""

from typing import List, Dict, Any, Tuple

# =============================================================================
# TEMPORAL SUBJECTS - 24 subjects spanning 2700 years
# =============================================================================

TEMPORAL_SUBJECTS: List[Dict[str, Any]] = [
    # === ANCIENT ERA (Pre-500 AD) ===
    {
        "id": "ancient_500bc",
        "name": "Ancient Greece 500BC",
        "year": -500,
        "month": 3,
        "day": 21,
        "hour": 12,
        "minute": 0,
        "lat": 37.9838,
        "lng": 23.7275,
        "tz_str": "Europe/Athens",
        "description": "Spring equinox in Ancient Greece",
    },
    {
        "id": "ancient_200bc",
        "name": "Ptolemaic Egypt 200BC",
        "year": -200,
        "month": 6,
        "day": 21,
        "hour": 12,
        "minute": 0,
        "lat": 30.0444,
        "lng": 31.2357,
        "tz_str": "Africa/Cairo",
        "description": "Summer solstice in Alexandria",
    },
    {
        "id": "roman_100ad",
        "name": "Roman Empire 100AD",
        "year": 100,
        "month": 1,
        "day": 1,
        "hour": 12,
        "minute": 0,
        "lat": 41.9028,
        "lng": 12.4964,
        "tz_str": "Europe/Rome",
        "description": "New Year in Rome",
    },
    {
        "id": "late_antiquity_400",
        "name": "Constantinople 400AD",
        "year": 400,
        "month": 12,
        "day": 25,
        "hour": 0,
        "minute": 0,
        "lat": 41.0082,
        "lng": 28.9784,
        "tz_str": "Europe/Istanbul",
        "description": "Christmas in Constantinople",
    },
    # === MEDIEVAL ERA (500-1450 AD) ===
    {
        "id": "early_medieval_800",
        "name": "Charlemagne Era 800AD",
        "year": 800,
        "month": 12,
        "day": 25,
        "hour": 12,
        "minute": 0,
        "lat": 50.0755,
        "lng": 14.4378,
        "tz_str": "Europe/Prague",
        "description": "Charlemagne coronation era",
    },
    {
        "id": "high_medieval_1100",
        "name": "Crusades Era 1100AD",
        "year": 1100,
        "month": 7,
        "day": 15,
        "hour": 12,
        "minute": 0,
        "lat": 48.8566,
        "lng": 2.3522,
        "tz_str": "Europe/Paris",
        "description": "High Middle Ages in Paris",
    },
    {
        "id": "late_medieval_1300",
        "name": "Dante Era 1300AD",
        "year": 1300,
        "month": 4,
        "day": 8,
        "hour": 12,
        "minute": 0,
        "lat": 43.7696,
        "lng": 11.2558,
        "tz_str": "Europe/Rome",
        "description": "Good Friday 1300 (Dante's Inferno)",
    },
    # === RENAISSANCE ERA (1450-1600) ===
    {
        "id": "early_renaissance_1450",
        "name": "Early Renaissance 1450",
        "year": 1450,
        "month": 6,
        "day": 15,
        "hour": 12,
        "minute": 0,
        "lat": 43.7696,
        "lng": 11.2558,
        "tz_str": "Europe/Rome",
        "description": "Florence in Early Renaissance",
    },
    {
        "id": "columbus_1492",
        "name": "Columbus 1492",
        "year": 1492,
        "month": 10,
        "day": 12,
        "hour": 6,
        "minute": 0,
        "lat": 24.0667,
        "lng": -74.5333,
        "tz_str": "America/Nassau",
        "description": "Columbus landfall in Bahamas",
    },
    {
        "id": "galileo_1564",
        "name": "Galileo Birth 1564",
        "year": 1564,
        "month": 2,
        "day": 15,
        "hour": 16,
        "minute": 0,
        "lat": 43.4643,
        "lng": 11.8818,
        "tz_str": "Europe/Rome",
        "description": "Galileo Galilei birth",
    },
    # === EARLY MODERN ERA (1600-1800) ===
    {
        "id": "newton_1643",
        "name": "Newton Birth 1643",
        "year": 1643,
        "month": 1,
        "day": 4,
        "hour": 2,
        "minute": 0,
        "lat": 52.9548,
        "lng": -0.5559,
        "tz_str": "Europe/London",
        "description": "Isaac Newton birth (Julian calendar)",
    },
    {
        "id": "enlightenment_1750",
        "name": "Enlightenment 1750",
        "year": 1750,
        "month": 7,
        "day": 4,
        "hour": 12,
        "minute": 0,
        "lat": 48.8566,
        "lng": 2.3522,
        "tz_str": "Europe/Paris",
        "description": "Paris during Enlightenment",
    },
    {
        "id": "american_independence_1776",
        "name": "US Independence 1776",
        "year": 1776,
        "month": 7,
        "day": 4,
        "hour": 17,
        "minute": 10,
        "lat": 39.9526,
        "lng": -75.1652,
        "tz_str": "America/New_York",
        "description": "Declaration of Independence signing",
    },
    # === 19TH CENTURY ===
    {
        "id": "industrial_1850",
        "name": "Industrial Era 1850",
        "year": 1850,
        "month": 6,
        "day": 15,
        "hour": 12,
        "minute": 0,
        "lat": 51.5074,
        "lng": -0.1278,
        "tz_str": "Europe/London",
        "description": "Victorian London",
    },
    {
        "id": "einstein_1879",
        "name": "Einstein Birth 1879",
        "year": 1879,
        "month": 3,
        "day": 14,
        "hour": 11,
        "minute": 30,
        "lat": 48.4011,
        "lng": 9.9876,
        "tz_str": "Europe/Berlin",
        "description": "Albert Einstein birth in Ulm",
    },
    # === 20TH CENTURY ===
    {
        "id": "ww1_start_1914",
        "name": "WW1 Start 1914",
        "year": 1914,
        "month": 7,
        "day": 28,
        "hour": 11,
        "minute": 0,
        "lat": 43.8563,
        "lng": 18.4131,
        "tz_str": "Europe/Sarajevo",
        "description": "Archduke assassination",
    },
    {
        "id": "john_lennon_1940",
        "name": "John Lennon",
        "year": 1940,
        "month": 10,
        "day": 9,
        "hour": 18,
        "minute": 30,
        "lat": 53.4084,
        "lng": -2.9916,
        "tz_str": "Europe/London",
        "description": "John Lennon birth - PRIMARY TEST SUBJECT",
    },
    {
        "id": "paul_mccartney_1942",
        "name": "Paul McCartney",
        "year": 1942,
        "month": 6,
        "day": 18,
        "hour": 15,
        "minute": 30,
        "lat": 53.4084,
        "lng": -2.9916,
        "tz_str": "Europe/London",
        "description": "Paul McCartney birth",
    },
    {
        "id": "johnny_depp_1963",
        "name": "Johnny Depp",
        "year": 1963,
        "month": 6,
        "day": 9,
        "hour": 0,
        "minute": 0,
        "lat": 37.7742,
        "lng": -87.1133,
        "tz_str": "America/Chicago",
        "description": "Johnny Depp birth - LEGACY TEST SUBJECT",
    },
    {
        "id": "yoko_ono_1933",
        "name": "Yoko Ono",
        "year": 1933,
        "month": 2,
        "day": 18,
        "hour": 10,
        "minute": 30,
        "lat": 35.6762,
        "lng": 139.6503,
        "tz_str": "Asia/Tokyo",
        "description": "Yoko Ono birth - for John+Yoko synastry",
    },
    # === 21ST CENTURY ===
    {
        "id": "millennium_2000",
        "name": "Millennium 2000",
        "year": 2000,
        "month": 1,
        "day": 1,
        "hour": 0,
        "minute": 0,
        "lat": 51.5074,
        "lng": -0.1278,
        "tz_str": "Europe/London",
        "description": "Y2K midnight in Greenwich",
    },
    {
        "id": "equinox_2020",
        "name": "Spring Equinox 2020",
        "year": 2020,
        "month": 3,
        "day": 20,
        "hour": 3,
        "minute": 50,
        "lat": 51.5074,
        "lng": -0.1278,
        "tz_str": "Europe/London",
        "description": "Vernal equinox 2020",
    },
    # === FUTURE ===
    {
        "id": "future_2050",
        "name": "Future 2050",
        "year": 2050,
        "month": 7,
        "day": 20,
        "hour": 12,
        "minute": 0,
        "lat": 35.6762,
        "lng": 139.6503,
        "tz_str": "Asia/Tokyo",
        "description": "Mid-21st century Tokyo",
    },
    {
        "id": "future_2100",
        "name": "Future 2100",
        "year": 2100,
        "month": 12,
        "day": 21,
        "hour": 12,
        "minute": 0,
        "lat": 40.7128,
        "lng": -74.0060,
        "tz_str": "America/New_York",
        "description": "Winter solstice 2100",
    },
    {
        "id": "future_2200",
        "name": "Future 2200",
        "year": 2200,
        "month": 1,
        "day": 1,
        "hour": 0,
        "minute": 0,
        "lat": 51.5074,
        "lng": -0.1278,
        "tz_str": "Europe/London",
        "description": "23rd century",
    },
]


# =============================================================================
# GEOGRAPHIC SUBJECTS - 15 locations covering all latitudes and longitudes
# =============================================================================

GEOGRAPHIC_SUBJECTS: List[Dict[str, Any]] = [
    # === HIGH NORTHERN LATITUDES (60°N - 66°N) ===
    {
        "id": "oslo_60n",
        "name": "Oslo 60N",
        "lat": 59.9139,
        "lng": 10.7522,
        "tz_str": "Europe/Oslo",
        "description": "High latitude, Northern Europe",
    },
    {
        "id": "reykjavik_64n",
        "name": "Reykjavik 64N",
        "lat": 64.1466,
        "lng": -21.9426,
        "tz_str": "Atlantic/Reykjavik",
        "description": "Near Arctic Circle, Iceland",
    },
    {
        "id": "arctic_circle_66n",
        "name": "Arctic Circle 66N",
        "lat": 66.0,
        "lng": 25.0,
        "tz_str": "Europe/Helsinki",
        "description": "Exactly at Arctic Circle limit",
    },
    # === MID NORTHERN LATITUDES (30°N - 60°N) ===
    {
        "id": "london_51n",
        "name": "London 51N",
        "lat": 51.5074,
        "lng": -0.1278,
        "tz_str": "Europe/London",
        "description": "Western Europe, Greenwich",
    },
    {
        "id": "new_york_40n",
        "name": "New York 40N",
        "lat": 40.7128,
        "lng": -74.0060,
        "tz_str": "America/New_York",
        "description": "Eastern USA",
    },
    {
        "id": "tokyo_35n",
        "name": "Tokyo 35N",
        "lat": 35.6762,
        "lng": 139.6503,
        "tz_str": "Asia/Tokyo",
        "description": "Eastern Asia, Japan",
    },
    # === EQUATORIAL LATITUDES (15°S - 15°N) ===
    {
        "id": "quito_equator",
        "name": "Quito Equator",
        "lat": 0.1807,
        "lng": -78.4678,
        "tz_str": "America/Guayaquil",
        "description": "Exactly at equator, Ecuador",
    },
    {
        "id": "singapore_1n",
        "name": "Singapore 1N",
        "lat": 1.3521,
        "lng": 103.8198,
        "tz_str": "Asia/Singapore",
        "description": "Near equator, Southeast Asia",
    },
    {
        "id": "nairobi_1s",
        "name": "Nairobi 1S",
        "lat": -1.2921,
        "lng": 36.8219,
        "tz_str": "Africa/Nairobi",
        "description": "Near equator, East Africa",
    },
    # === MID SOUTHERN LATITUDES (30°S - 60°S) ===
    {
        "id": "sydney_34s",
        "name": "Sydney 34S",
        "lat": -33.8688,
        "lng": 151.2093,
        "tz_str": "Australia/Sydney",
        "description": "Southern Hemisphere, Australia",
    },
    {
        "id": "buenos_aires_34s",
        "name": "Buenos Aires 34S",
        "lat": -34.6037,
        "lng": -58.3816,
        "tz_str": "America/Argentina/Buenos_Aires",
        "description": "Southern Hemisphere, South America",
    },
    {
        "id": "cape_town_34s",
        "name": "Cape Town 34S",
        "lat": -33.9249,
        "lng": 18.4241,
        "tz_str": "Africa/Johannesburg",
        "description": "Southern Hemisphere, Africa",
    },
    # === HIGH SOUTHERN LATITUDES (55°S - 66°S) ===
    {
        "id": "ushuaia_55s",
        "name": "Ushuaia 55S",
        "lat": -54.8019,
        "lng": -68.3030,
        "tz_str": "America/Argentina/Ushuaia",
        "description": "Southernmost city, Tierra del Fuego",
    },
    {
        "id": "antarctic_circle_66s",
        "name": "Antarctic Circle 66S",
        "lat": -66.0,
        "lng": 110.0,
        "tz_str": "Antarctica/Casey",
        "description": "Exactly at Antarctic Circle limit",
    },
    # === DATE LINE / EXTREME LONGITUDES ===
    {
        "id": "fiji_dateline_east",
        "name": "Fiji Dateline East",
        "lat": -18.1416,
        "lng": 178.4419,
        "tz_str": "Pacific/Fiji",
        "description": "Near International Date Line (east)",
    },
    {
        "id": "samoa_dateline_west",
        "name": "Samoa Dateline West",
        "lat": -13.8333,
        "lng": -171.75,
        "tz_str": "Pacific/Samoa",
        "description": "Near International Date Line (west)",
    },
]


# =============================================================================
# HOUSE SYSTEMS - All supported systems
# =============================================================================

HOUSE_SYSTEMS: List[str] = [
    "P",  # Placidus (default)
    "K",  # Koch
    "O",  # Porphyry
    "R",  # Regiomontanus
    "C",  # Campanus
    "A",  # Equal (cusp 1 is Ascendant)
    "V",  # Vehlow Equal
    "W",  # Whole Sign
    "X",  # Axial Rotation / Meridian
    "H",  # Horizon / Azimuth
    "T",  # Polich/Page (Topocentric)
    "B",  # Alcabitius
    "M",  # Morinus
    "U",  # Krusinski-Pisa
    "D",  # Equal (MC)
    "F",  # Carter poli-equ.
    "I",  # Sunshine
    "i",  # Sunshine/alt.
    "L",  # Pullen SD
    "N",  # Equal/1=Aries
    "Q",  # Pullen SR
    "S",  # Sripati
    "Y",  # APC houses
]


# =============================================================================
# SIDEREAL MODES - All 20 supported ayanamsas
# =============================================================================

SIDEREAL_MODES: List[str] = [
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
    "J1900",
    "J2000",
    "B1950",
]


# =============================================================================
# SYNASTRY PAIRS - Pairs of subjects for synastry testing
# =============================================================================

SYNASTRY_PAIRS: List[Tuple[str, str]] = [
    ("john_lennon_1940", "paul_mccartney_1942"),  # Beatles duo
    ("john_lennon_1940", "yoko_ono_1933"),  # John + Yoko - historic pair
    ("johnny_depp_1963", "john_lennon_1940"),  # Cross-generation
    ("einstein_1879", "galileo_1564"),  # Scientists (different eras)
    ("millennium_2000", "equinox_2020"),  # Modern era
    ("ancient_500bc", "roman_100ad"),  # Ancient era
]


# =============================================================================
# PERSPECTIVE TYPES
# =============================================================================

PERSPECTIVE_TYPES: List[str] = [
    "Apparent Geocentric",  # Default
    "True Geocentric",
    "Heliocentric",
    "Topocentric",
]


# =============================================================================
# PLANETS AND POINTS
# =============================================================================

CORE_PLANETS: List[str] = [
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
]

LUNAR_NODES: List[str] = [
    "mean_north_lunar_node",
    "true_north_lunar_node",
    "mean_south_lunar_node",
    "true_south_lunar_node",
]

ANGLES: List[str] = [
    "ascendant",
    "descendant",
    "medium_coeli",
    "imum_coeli",
]

HOUSES: List[str] = [
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
]

ALL_POINTS: List[str] = CORE_PLANETS + LUNAR_NODES + ANGLES


# =============================================================================
# POINT ATTRIBUTES TO TEST
# =============================================================================

POINT_NUMERIC_ATTRS: List[str] = [
    "abs_pos",
    "position",
]

POINT_STRING_ATTRS: List[str] = [
    "name",
    "sign",
    "element",
    "quality",
    "emoji",
    "house",
]

POINT_INT_ATTRS: List[str] = [
    "sign_num",
]

POINT_BOOL_ATTRS: List[str] = [
    "retrograde",
]

PLANET_EXTRA_ATTRS: List[str] = [
    "speed",
    "declination",
]


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def get_subject_by_id(subject_id: str) -> Dict[str, Any]:
    """Get a temporal or geographic subject by its ID."""
    for subject in TEMPORAL_SUBJECTS:
        if subject["id"] == subject_id:
            return subject
    for subject in GEOGRAPHIC_SUBJECTS:
        if subject["id"] == subject_id:
            return subject
    raise ValueError(f"Subject with id '{subject_id}' not found")


def get_temporal_subject_ids() -> List[str]:
    """Get list of all temporal subject IDs."""
    return [s["id"] for s in TEMPORAL_SUBJECTS]


def get_geographic_subject_ids() -> List[str]:
    """Get list of all geographic subject IDs."""
    return [s["id"] for s in GEOGRAPHIC_SUBJECTS]


def get_primary_test_subjects() -> List[str]:
    """Get IDs of primary test subjects (most commonly used)."""
    return [
        "john_lennon_1940",
        "johnny_depp_1963",
        "paul_mccartney_1942",
    ]


def get_extreme_latitude_subjects() -> List[str]:
    """Get IDs of subjects at extreme latitudes for edge case testing."""
    return [
        "arctic_circle_66n",
        "antarctic_circle_66s",
        "reykjavik_64n",
        "ushuaia_55s",
    ]


def get_equatorial_subjects() -> List[str]:
    """Get IDs of subjects near the equator."""
    return [
        "quito_equator",
        "singapore_1n",
        "nairobi_1s",
    ]
