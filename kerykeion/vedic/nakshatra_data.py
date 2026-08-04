# -*- coding: utf-8 -*-
"""The 27 Nakshatras (Vedic lunar mansions).

Each nakshatra spans 13°20' (13.333... degrees) of the sidereal zodiac,
giving 27 equal divisions of the 360° circle. Each nakshatra is further
divided into 4 padas (quarters) of 3°20' (3.333... degrees) each.

The Vimsottari Dasha lords follow a fixed repeating sequence:
Ketu, Venus, Sun, Moon, Mars, Rahu, Jupiter, Saturn, Mercury
(repeating 3 times for 27 nakshatras).

Sources:
    - B.V. Raman, Hindu Predictive Astrology
    - K.S. Charak, Elements of Vedic Astrology
"""

from typing import List, Tuple

# Vimsottari Dasha lord sequence (repeats 3 times for 27 nakshatras)
_DASHA_LORDS = [
    "Ketu", "Venus", "Sun", "Moon", "Mars",
    "Rahu", "Jupiter", "Saturn", "Mercury",
]

# Each entry: (name, deity)
# Spans are computed from index: start = i * 13.3333..., end = (i+1) * 13.3333...
NAKSHATRAS: List[Tuple[str, str]] = [
    ("Ashwini", "Ashwini Kumaras"),
    ("Bharani", "Yama"),
    ("Krittika", "Agni"),
    ("Rohini", "Brahma"),
    ("Mrigashira", "Soma"),
    ("Ardra", "Rudra"),
    ("Punarvasu", "Aditi"),
    ("Pushya", "Brihaspati"),
    ("Ashlesha", "Nagas"),
    ("Magha", "Pitris"),
    ("Purva Phalguni", "Bhaga"),
    ("Uttara Phalguni", "Aryaman"),
    ("Hasta", "Savitar"),
    ("Chitra", "Vishvakarma"),
    ("Swati", "Vayu"),
    ("Vishakha", "Indra-Agni"),
    ("Anuradha", "Mitra"),
    ("Jyeshtha", "Indra"),
    ("Mula", "Nirriti"),
    ("Purva Ashadha", "Apas"),
    ("Uttara Ashadha", "Vishvedevas"),
    ("Shravana", "Vishnu"),
    ("Dhanishtha", "Vasus"),
    ("Shatabhisha", "Varuna"),
    ("Purva Bhadrapada", "Aja Ekapada"),
    ("Uttara Bhadrapada", "Ahir Budhnya"),
    ("Revati", "Pushan"),
]

# Span of each nakshatra in degrees
NAKSHATRA_SPAN = 360.0 / 27.0  # 13.333...
PADA_SPAN = NAKSHATRA_SPAN / 4.0  # 3.333...


def get_dasha_lord(nakshatra_index: int) -> str:
    """Return the Vimsottari Dasha lord for the given nakshatra (0-based index)."""
    return _DASHA_LORDS[nakshatra_index % 9]
