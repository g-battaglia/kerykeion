# -*- coding: utf-8 -*-
"""Reference tables for the Ptolemaic essential dignity system.

Sources:
    - Ptolemy, Tetrabiblos (2nd century CE)
    - William Lilly, Christian Astrology (1647)
    - Robert Hand, Night & Day (2009)

All tables use the 3-letter sign abbreviations from kr_literals.Sign.
"""

from typing import Dict, List, Optional, Tuple

# =========================================================================
# DOMICILE (Rulership) — planet rules the sign
# Traditional + modern rulerships. Score: +5
# =========================================================================
DOMICILE_RULERS: Dict[str, List[str]] = {
    "Ari": ["Mars"],
    "Tau": ["Venus"],
    "Gem": ["Mercury"],
    "Can": ["Moon"],
    "Leo": ["Sun"],
    "Vir": ["Mercury"],
    "Lib": ["Venus"],
    "Sco": ["Mars"],       # Traditional: Mars (modern co-ruler: Pluto)
    "Sag": ["Jupiter"],
    "Cap": ["Saturn"],
    "Aqu": ["Saturn"],     # Traditional: Saturn (modern co-ruler: Uranus)
    "Pis": ["Jupiter"],    # Traditional: Jupiter (modern co-ruler: Neptune)
}

# =========================================================================
# DETRIMENT — planet is in the sign opposite its domicile. Score: -5
# =========================================================================
DETRIMENT_RULERS: Dict[str, List[str]] = {
    "Ari": ["Venus"],
    "Tau": ["Mars"],
    "Gem": ["Jupiter"],
    "Can": ["Saturn"],
    "Leo": ["Saturn"],
    "Vir": ["Jupiter"],
    "Lib": ["Mars"],
    "Sco": ["Venus"],
    "Sag": ["Mercury"],
    "Cap": ["Moon"],
    "Aqu": ["Sun"],
    "Pis": ["Mercury"],
}

# =========================================================================
# EXALTATION — planet is exalted in a specific sign (with traditional degree)
# Score: +4
# =========================================================================
EXALTATION_TABLE: Dict[str, Tuple[str, Optional[int]]] = {
    # sign -> (planet, exact_degree_or_None)
    "Ari": ("Sun", 19),
    "Tau": ("Moon", 3),
    "Gem": (None, None),       # No classical exaltation
    "Can": ("Jupiter", 15),
    "Leo": (None, None),
    "Vir": ("Mercury", 15),
    "Lib": ("Saturn", 21),
    "Sco": (None, None),
    "Sag": (None, None),
    "Cap": ("Mars", 28),
    "Aqu": (None, None),
    "Pis": ("Venus", 27),
}

# =========================================================================
# FALL — opposite of exaltation. Score: -4
# =========================================================================
FALL_TABLE: Dict[str, Optional[str]] = {
    "Ari": "Saturn",
    "Tau": None,
    "Gem": None,
    "Can": "Mars",
    "Leo": None,
    "Vir": "Venus",
    "Lib": "Sun",
    "Sco": "Moon",
    "Sag": None,
    "Cap": "Jupiter",
    "Aqu": None,
    "Pis": "Mercury",
}

# =========================================================================
# TRIPLICITY RULERS — by element, day/night sect
# Dorothean system (most widely used). Score: +3
# =========================================================================
TRIPLICITY_RULERS: Dict[str, Dict[str, str]] = {
    # element -> {"day": planet, "night": planet, "participating": planet}
    "Fire": {"day": "Sun", "night": "Jupiter", "participating": "Saturn"},
    "Earth": {"day": "Venus", "night": "Moon", "participating": "Mars"},
    "Air": {"day": "Saturn", "night": "Mercury", "participating": "Jupiter"},
    "Water": {"day": "Venus", "night": "Mars", "participating": "Moon"},
}

# =========================================================================
# EGYPTIAN TERMS (Bounds) — Ptolemy's version
# Each sign is divided into 5 unequal segments ruled by a planet.
# Score: +2
# =========================================================================
# Format: sign -> list of (ruler, start_degree, end_degree)
EGYPTIAN_TERMS: Dict[str, List[Tuple[str, int, int]]] = {
    "Ari": [("Jupiter", 0, 6), ("Venus", 6, 12), ("Mercury", 12, 20), ("Mars", 20, 25), ("Saturn", 25, 30)],
    "Tau": [("Venus", 0, 8), ("Mercury", 8, 14), ("Jupiter", 14, 22), ("Saturn", 22, 27), ("Mars", 27, 30)],
    "Gem": [("Mercury", 0, 6), ("Jupiter", 6, 12), ("Venus", 12, 17), ("Mars", 17, 24), ("Saturn", 24, 30)],
    "Can": [("Mars", 0, 7), ("Venus", 7, 13), ("Mercury", 13, 19), ("Jupiter", 19, 26), ("Saturn", 26, 30)],
    "Leo": [("Jupiter", 0, 6), ("Venus", 6, 11), ("Saturn", 11, 18), ("Mercury", 18, 24), ("Mars", 24, 30)],
    "Vir": [("Mercury", 0, 7), ("Venus", 7, 17), ("Jupiter", 17, 21), ("Mars", 21, 28), ("Saturn", 28, 30)],
    "Lib": [("Saturn", 0, 6), ("Mercury", 6, 14), ("Jupiter", 14, 21), ("Venus", 21, 28), ("Mars", 28, 30)],
    "Sco": [("Mars", 0, 7), ("Venus", 7, 11), ("Mercury", 11, 19), ("Jupiter", 19, 24), ("Saturn", 24, 30)],
    "Sag": [("Jupiter", 0, 12), ("Venus", 12, 17), ("Mercury", 17, 21), ("Saturn", 21, 26), ("Mars", 26, 30)],
    "Cap": [("Mercury", 0, 7), ("Jupiter", 7, 14), ("Venus", 14, 22), ("Saturn", 22, 26), ("Mars", 26, 30)],
    "Aqu": [("Mercury", 0, 7), ("Venus", 7, 13), ("Jupiter", 13, 20), ("Mars", 20, 25), ("Saturn", 25, 30)],
    "Pis": [("Venus", 0, 12), ("Jupiter", 12, 16), ("Mercury", 16, 19), ("Mars", 19, 28), ("Saturn", 28, 30)],
}

# =========================================================================
# CHALDEAN DECANS (Faces) — 36 decans in Chaldean planetary order
# Each sign divided into 3 decans of 10 degrees.
# Chaldean order: Saturn, Jupiter, Mars, Sun, Venus, Mercury, Moon (repeating)
# Score: +1
# =========================================================================
_CHALDEAN_ORDER = ["Mars", "Sun", "Venus", "Mercury", "Moon", "Saturn", "Jupiter"]

CHALDEAN_DECANS: Dict[str, List[str]] = {}
_sign_order = ["Ari", "Tau", "Gem", "Can", "Leo", "Vir", "Lib", "Sco", "Sag", "Cap", "Aqu", "Pis"]
for _i, _sign in enumerate(_sign_order):
    _base = _i * 3
    CHALDEAN_DECANS[_sign] = [
        _CHALDEAN_ORDER[(_base + 0) % 7],
        _CHALDEAN_ORDER[(_base + 1) % 7],
        _CHALDEAN_ORDER[(_base + 2) % 7],
    ]

# Planets that can have essential dignities (classical 7 only)
DIGNITY_PLANETS = {"Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn"}
